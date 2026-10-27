#!/usr/bin/env python3
"""Descarga un vídeo protegido por login (p. ej. del campus de EBIS / Blackboard) con un Chrome controlado por Playwright.

Abre una ventana de Chrome con un perfil propio; si el campus pide login, el usuario inicia sesión a mano en esa
ventana. En cuanto el navegador recibe el vídeo (respuesta video/* o descarga), el script toma su URL final y las
cookies de la sesión y lo descarga en streaming a disco (reanudable). Las cookies nunca se imprimen ni se guardan
fuera del perfil.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from playwright.sync_api import BrowserContext, Download, Error, Page, Response, sync_playwright
except ImportError:
    raise SystemExit("error: falta playwright en el .venv compartido (python3 ../scripts/setup_env.py)")

DEFAULT_PROFILE = Path.home() / ".cache" / "skills-mario" / "campus-chrome-profile"
MEDIA_TYPES = ("video/", "audio/", "application/octet-stream", "application/mp4")
LOGIN_HINTS = ("login", "auth", "sso", "saml", "signin", "oauth", "adfs")
EXTENSIONS = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov", "audio/mpeg": ".mp3",
              "audio/mp4": ".m4a", "video/x-matroska": ".mkv"}
CHUNK = 1 << 20


@dataclass(slots=True)
class Media:
    url: str
    content_type: str
    filename: str | None


def _filename_from_disposition(value: str) -> str | None:
    if m := re.search(r"filename\*=(?:UTF-8'')?([^;]+)", value, re.I):
        return unquote(m.group(1).strip('" '))
    if m := re.search(r'filename="?([^";]+)"?', value, re.I):
        return m.group(1).strip()
    return None


def _as_media(response: Response) -> Media | None:
    headers = response.headers
    ctype = headers.get("content-type", "").split(";")[0].strip().lower()
    disposition = headers.get("content-disposition", "")
    if response.status >= 400 or not (ctype.startswith(MEDIA_TYPES) or "attachment" in disposition.lower()):
        return None
    return Media(response.url, ctype, _filename_from_disposition(disposition))


def _is_login_page(url: str) -> bool:
    return any(h in url.lower() for h in LOGIN_HINTS)


def _video_in_dom(context: BrowserContext) -> tuple[Media, Page] | None:
    """Busca <video>/<source> en todas las pestañas y frames: el campus incrusta el vídeo en una página HTML
    sin autoplay, así que el navegador no llega a pedirlo y no aparece como respuesta de red."""
    for page in context.pages:
        for frame in page.frames:
            try:
                srcs = frame.evaluate(_DOM_SCAN)
            except Error:  # frame navegando o cerrado
                continue
            if srcs:
                return Media(srcs[0], "", None), page
    return None


_DOM_SCAN = """() => [...document.querySelectorAll('video, video source')]
    .map(e => e.currentSrc || e.src).filter(s => s && !s.startsWith('blob:'))"""


def _wait_for_media(context: BrowserContext, page: Page, target: str, timeout: float,
                    login_url: str | None) -> tuple[Media | None, Download | None, Page]:
    found: list[tuple[Media, Page]] = []
    downloads: list[Download] = []

    def watch(p: Page) -> None:  # Playwright no admite métodos builtin (list.append) como handler
        p.on("response", lambda r: (m := _as_media(r)) and found.append((m, p)))
        p.on("download", lambda d: downloads.append(d))

    for p in context.pages:
        watch(p)
    context.on("page", watch)  # el usuario puede abrir el vídeo en otra pestaña

    def go() -> int:
        """Abre el vídeo y devuelve el código HTTP (0 si no hay respuesta, p. ej. una descarga)."""
        try:
            response = page.goto(target, wait_until="commit")
            return response.status if response else 0
        except Error as e:  # «Download is starting»: el fichero llega por el evento download
            if "Download is starting" not in str(e):
                print(f"aviso: {e.message.splitlines()[0]}")
            return 0

    print("➡ Si la ventana de Chrome pide login, inicia sesión ahí. Si después no se abre el vídeo, ábrelo tú "
          f"en esa ventana (cualquier pestaña). Espero hasta {int(timeout // 60)} min.", flush=True)
    seen_login = reloaded_after_login = False
    if (status := go()) >= 400:  # 401/404: el enlace existe pero no hay sesión
        print(f"· El vídeo responde HTTP {status}: falta iniciar sesión.", flush=True)
        seen_login = True
        if login_url:
            page.goto(login_url, wait_until="commit")
    deadline = time.monotonic() + timeout
    last_urls: set[str] = set()
    while time.monotonic() < deadline:
        if downloads:
            return None, downloads[0], page
        if found:
            return found[0][0], None, found[0][1]
        if hit := _video_in_dom(context):
            return hit[0], None, hit[1]
        urls = {_short(p.url) for p in context.pages}
        for url in sorted(urls - last_urls):  # rastro para diagnosticar (sin query: lleva hashes y tokens)
            print(f"· página: {url}", flush=True)
        last_urls = urls
        if _is_login_page(page.url) or (login_url and _short(page.url) == _short(login_url)):
            seen_login, reloaded_after_login = True, False
        elif seen_login and not reloaded_after_login:
            # tras el login el campus suele llevar a la portada: volvemos a pedir el vídeo
            reloaded_after_login = True
            page.wait_for_timeout(2000)
            if not (found or downloads):
                go()
        page.wait_for_timeout(1000)
    return None, None, page


def _short(url: str) -> str:
    parts = urlparse(url)
    return f"{parts.netloc}{parts.path}" if parts.netloc else url


def _stream(media: Media, context: BrowserContext, user_agent: str, referer: str, dest: Path) -> int:
    part = dest.with_suffix(dest.suffix + ".part")
    cookies = "; ".join(f"{c['name']}={c['value']}" for c in context.cookies(media.url))
    headers = {"User-Agent": user_agent, "Referer": referer, "Accept": "*/*"}
    if cookies:
        headers["Cookie"] = cookies
    start = part.stat().st_size if part.exists() else 0
    if start:
        headers["Range"] = f"bytes={start}-"
    request = urllib.request.Request(media.url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as resp:
        if start and resp.status != 206:  # el servidor no admite reanudar: empezamos de cero
            start = 0
        total = int(resp.headers.get("Content-Length", 0)) + start
        done = start
        last = 0.0
        with part.open("ab" if start else "wb") as fh:
            while chunk := resp.read(CHUNK):
                fh.write(chunk)
                done += len(chunk)
                if time.monotonic() - last > 2:
                    pct = f" ({done * 100 / total:.0f} %)" if total else ""
                    print(f"  {done / 1e6:,.1f} MB{pct}", flush=True)
                    last = time.monotonic()
    if total and done != total:
        raise SystemExit(f"error: descarga incompleta ({done} de {total} bytes); vuelve a ejecutar para reanudar")
    part.rename(dest)
    return done


def _pick_name(media: Media | None, download: Download | None, name: str | None) -> str:
    base = name or (download.suggested_filename if download else None) or (media and media.filename)
    if not base and media:
        base = Path(unquote(urlparse(media.url).path)).name
    base = base or "video"
    if not Path(base).suffix:
        base += EXTENSIONS.get(media.content_type if media else "", ".mp4")
    return re.sub(r'[\\/:*?"<>|]+', "_", base)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", help="nombre del fichero de salida (por defecto, el del servidor)")
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE,
                        help="perfil de Chrome (guarda la sesión entre ejecuciones; fuera del repo)")
    parser.add_argument("--login-timeout", type=float, default=600, help="segundos máximos esperando al vídeo")
    parser.add_argument("--login-url", help="página de login a abrir si el vídeo da 401/404 sin sesión "
                        "(EBIS: https://campusvirtual.ebiseducation.com/)")
    parser.add_argument("--headless", action="store_true", help="sin ventana (solo si la sesión ya está iniciada)")
    parser.add_argument("--force", action="store_true", help="sobrescribe si el fichero ya existe")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.profile_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                str(args.profile_dir), channel="chrome", headless=args.headless, accept_downloads=True)
        except Error:
            context = p.chromium.launch_persistent_context(  # sin Chrome del sistema: Chromium de Playwright
                str(args.profile_dir), headless=args.headless, accept_downloads=True)
        page = context.pages[0] if context.pages else context.new_page()
        media, download, page = _wait_for_media(context, page, args.url, args.login_timeout, args.login_url)
        if not media and not download:
            shot = args.output_dir / "sin_video.png"
            page.screenshot(path=str(shot))
            context.close()
            raise SystemExit(f"error: no llegó ningún vídeo en {args.login_timeout:.0f} s. Captura: {shot}")

        dest = args.output_dir / _pick_name(media, download, args.name)
        if dest.exists() and not args.force:
            context.close()
            raise SystemExit(f"error: ya existe {dest} (usa --force)")
        print(f"🎬 Vídeo encontrado → {dest}")
        if download:
            download.save_as(str(dest))
            size, final_url, ctype = dest.stat().st_size, download.url, ""
        else:
            assert media is not None
            user_agent = page.evaluate("navigator.userAgent")
            referer = page.url
            page.goto("about:blank")  # que el reproductor no siga bajando el vídeo en paralelo
            size = _stream(media, context, user_agent, referer, dest)
            final_url, ctype = media.url, media.content_type
        context.close()

    manifest = {"source_url": args.url, "final_url": final_url.split("?")[0], "file": dest.name,
                "bytes": size, "content_type": ctype}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"✅ {dest} ({size / 1e6:,.1f} MB)")


if __name__ == "__main__":
    sys.exit(main())
