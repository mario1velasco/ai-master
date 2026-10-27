# Errores conocidos — campus-video-download

Formato: síntoma, causa, solución y prevención (ver `../../CLAUDE.md`).

## Handler de evento con un método builtin (2026-10-27)
- **Síntoma:** `AttributeError: 'builtin_function_or_method' object has no attribute '_pw_impl_instance_'` en `page.on("download", downloads.append)`.
- **Causa:** Playwright guarda un atributo en la función handler; los métodos builtin (`list.append`) no admiten atributos.
- **Solución:** envolver en una lambda: `page.on("download", lambda d: downloads.append(d))` (`scripts/download_video.py`, `_wait_for_media`).
- **Prevención:** usar siempre funciones Python (def/lambda) como handlers de `page.on(...)`.

## El script espera para siempre con el vídeo visible en Chrome (2026-10-27)
- **Síntoma:** la ventana muestra el vídeo (URL `alt-….blackboard.com/bbcswebdav/…/embedded/UNSAFE_HTML/UNSAFE_HTML_….html?one_hash=…&f_hash=…`) pero el script no imprime nada ni descarga.
- **Causa:** el enlace `xid-…` del campus no sirve el vídeo directamente: tras el login abre una página HTML con un `<video>` sin autoplay, en otro dominio y a veces en otra pestaña. El navegador no llega a pedir el fichero, así que no hay respuesta `video/*` que detectar. Además la URL del login de EBIS no siempre contiene `login`, y el aviso de iniciar sesión no salía.
- **Solución:** `_wait_for_media` vigila todas las pestañas (`context.on("page")`) y busca `<video>`/`<source>` en el DOM de cada frame (`_video_in_dom`); el aviso de login se imprime siempre al arrancar (`scripts/download_video.py`).
- **Prevención:** no depender solo de respuestas de red. Las cookies del campus son de sesión: si se cierra la ventana, hay que volver a iniciar sesión (los enlaces devuelven 404/401 fuera de la sesión).

## Se usó un Chrome nuevo en vez del Chrome con la sesión (2026-10-27)
- **Síntoma:** la ventana de Playwright mostraba el login o la página del campus de un perfil vacío; el usuario ya estaba logueado en su Chrome normal y tenía que volver a entrar. Al cerrar la ventana la sesión se perdía (cookies de sesión) y los enlaces daban 404/401.
- **Causa:** `download_video.py` abre Chrome con un perfil propio (Chrome no deja automatizar el perfil por defecto mientras está abierto).
- **Solución:** el método principal pasa a ser `yt-dlp --cookies-from-browser chrome`, que reutiliza la sesión del Chrome del usuario sin abrir otro navegador (`SKILL.md`, pasos 2-3). Playwright queda como alternativa.
- **Prevención:** usar siempre primero las cookies del Chrome del usuario; avisar antes si hay que recurrir a un perfil aparte.

## ffmpeg falla con el HLS de Bunny Stream (2026-10-27)
- **Síntoma:** `WARNING: The stream has AES-128 encryption and pycryptodomex is not available; extraction will be delegated to ffmpeg` y luego `video0.dts is not in allowed_segment_extensions` → `ERROR: ffmpeg exited with code 183`.
- **Causa:** los vídeos del campus de EBIS están en Bunny Stream (`iframe.mediadelivery.net`), en HLS con cifrado AES-128 estándar y segmentos `.dts`. Sin `pycryptodomex`, yt-dlp delega en ffmpeg, y las versiones recientes de ffmpeg rechazan esa extensión de segmento.
- **Solución:** instalar `pycryptodomex` en el `.venv` (fijado en `requirements.txt`): yt-dlp descarga y descifra los segmentos con su descargador nativo (`hlsnative`).
- **Prevención:** `setup_env.py` comprueba el import `Cryptodome`. Si vuelve a salir el aviso de «delegated to ffmpeg», falta esa dependencia.
