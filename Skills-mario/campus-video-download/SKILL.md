---
name: campus-video-download
description: >
  Descarga vídeos (o audios) que están detrás de un login web, como las clases
  grabadas del campus virtual de EBIS (Blackboard, enlaces bbcswebdav/xid-… o
  …/embedded/UNSAFE_HTML/….html), usando la sesión del Chrome en el que el
  usuario ya ha iniciado sesión (cookies leídas con yt-dlp). Actívala cuando
  pidan descargar o bajar un vídeo/grabación de clase del campus, de Blackboard
  o de cualquier web que requiera iniciar sesión, o cuando se proponga usar
  Playwright para descargar un vídeo.
---

# Campus Video Download

Descarga un vídeo protegido por login **con la sesión del Chrome normal del usuario**, sin pedirle la contraseña ni abrir otro navegador: `yt-dlp --cookies-from-browser chrome` lee y descifra las cookies del perfil de Chrome (llavero de GNOME vía `secretstorage`), abre la página del campus, encuentra el `<video>` incrustado y lo descarga. Ejecuta desde esta carpeta con el `.venv` compartido:

```bash
PY="$(git rev-parse --show-toplevel)/.venv/bin/python"
YTDLP="$(git rev-parse --show-toplevel)/.venv/bin/yt-dlp"
```

Requisitos: `yt-dlp` y `secretstorage` en el `.venv` (`python3 ../scripts/setup_env.py`), Google Chrome con la sesión del campus iniciada y `ffprobe` para verificar.

> **No uses un Chrome nuevo o privado para esto** (es el error que ya se cometió, ver `references/errores_conocidos.md`): un perfil vacío no tiene la sesión, y las cookies del campus son de sesión, así que se pierden al cerrar esa ventana. Usa siempre el Chrome en el que el usuario ya está logueado.

## Flujo de trabajo

1. **Confirma la entrada.** URL y carpeta de salida. La URL que mejor funciona es la de la página del vídeo que el usuario ve en su Chrome (EBIS: `https://alt-….blackboard.com/bbcswebdav/…/embedded/UNSAFE_HTML/UNSAFE_HTML_….html?one_hash=…&f_hash=…`); pídesela si solo tienes un enlace `xid-…` y este falla. Si la carpeta está dentro de un repo git, comprueba que los vídeos quedan ignorados (`git check-ignore`); si no, propón un `.gitignore` en esa carpeta.
2. **Prueba sin descargar** (comprueba sesión, nombre y duración):
   ```bash
   $YTDLP --cookies-from-browser chrome --simulate --print "%(title)s | %(ext)s | %(duration_string)s" "URL"
   ```
   Si da 401/404 o «Unsupported URL», el usuario no tiene la sesión abierta en Chrome (que entre en el campus y abra el vídeo) o la URL no es la de la página del vídeo. Si Chrome tiene varios perfiles: `--cookies-from-browser "chrome:Profile 1"`. Puede saltar un aviso del llavero pidiendo permiso: es normal.
3. **Descarga en segundo plano** (una clase de 2,5 h son cientos de MB):
   ```bash
   $YTDLP --cookies-from-browser chrome --newline --no-mtime -o "SALIDA/<nombre>.%(ext)s" "URL"
   ```
   Si se corta, repite el mismo comando: yt-dlp reanuda el `.part`.
4. **Verifica.** `$PY scripts/check_video.py SALIDA/<nombre>.mp4` comprueba que no queda `.part` y que `ffprobe` lee el vídeo con duración razonable y pista de audio. Compara la duración con la del paso 2.
5. **Entrega.** Ruta, tamaño y duración. Si el usuario quiere el contenido de la clase: extraer el audio (`ffmpeg -i video.mp4 -vn -c:a copy audio.m4a`) y pasarlo por **media-resume** o **audio-split** + **audio-decoder**.

## Alternativa: `scripts/download_video.py` (Playwright)

Solo si no se pueden leer las cookies de Chrome (otro sistema, llavero bloqueado). Abre **su propio Chrome con un perfil aparte** (`~/.cache/skills-mario/campus-chrome-profile`), en el que el usuario tiene que iniciar sesión otra vez; avísale antes. Detecta el vídeo en cualquier pestaña (respuesta `video/*`, descarga o `<video>` en la página) y lo baja en streaming.

```bash
$PY -u scripts/download_video.py "URL" --output-dir SALIDA --name clase.mp4 --login-url https://campusvirtual.ebiseducation.com/
$PY scripts/check_video.py SALIDA
```

Imprime las páginas por las que pasa (sin query) para diagnosticar. Al pararlo, cierra también su Chrome (`pkill -f 'user-data-dir=/home/mario/.cache/skills-mari[o]'`: el corchete evita que `pkill` mate a la propia shell). Si no, la siguiente ejecución falla con `ProcessSingleton`.

## Seguridad

- Las cookies solo las usa yt-dlp en memoria: no las exportes a ficheros (`--cookies`), no las imprimas y no las pegues en el chat. Al mostrar URLs firmadas en logs, quita la query (`one_hash`, `f_hash`, firmas).
- Descarga solo material al que el usuario tiene acceso legítimo y para su uso personal.

Fallos ya vistos (y dónde documentar los nuevos): `references/errores_conocidos.md`.
