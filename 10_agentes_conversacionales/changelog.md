# Changelog — Tema 10 · Agentes conversacionales (kit `ondo-agente`)

Todo lo que ha hecho falta para poner a funcionar `ondo-agente`, siguiendo la
**Guía de Ejercicio de Clase · Día 1 · Agente de chat en Telegram** (`clase_01/`).
Lo más reciente, arriba.

## Pendiente (lo hace Mario)

Siguen el orden de la guía del día 1:

1. **Clave de OpenAI** (guía, apartado 2): abrir `ondo-agente/.env` y pegarla detrás de
   `OPENAI_API_KEY=` (sin espacios ni comillas). Después, con el entorno activado:
   `python scripts/comprobar_entorno.py` → debe terminar en «Todo listo» (el aviso de ngrok
   no importa hasta el día 3).
2. **Bot de Telegram** (paso 1): en Telegram, `@BotFather` → `/newbot` → nombre → username
   acabado en `bot`. Pegar el token en `.env` detrás de `TELEGRAM_BOT_TOKEN=`.
3. **Arrancar el bot** (paso 2): `python -m canales.telegram_bot` → debe salir
   «Bot @… listo». Probar `¿Dónde está mi pedido?` + `lucia.martin@example.com` y los botones
   tras un `Hola`.
4. **Entender el agente** (paso 3): preguntas al chat de VS Code en modo *Ask* y las cuatro
   pruebas con `python -m canales.consola --traza` (memoria, seguridad, pedido ajeno,
   reparación).
5. **AGENTS.md, skill y subagente** (paso 4): abrir los tres ficheros y contrastarlos con el chat.

## 2026-11-24 — Entorno del kit listo (falta la clave)

- Comprobado que no hay cambios nuevos del profesor (`git fetch`: el kit sigue en `43dafbd`).
- Creado `ondo-agente/.venv` con **Python 3.12.13** (el recomendado). Se usa el CPython 3.12
  que instaló uv, no el `python3` de la terminal, que apuntaba al `.venv` de `travel-agency`.
- Instaladas las dependencias: `python -m pip install -r requirements.txt`.
- Copiado `.env.example` a `.env` (todavía sin clave ni token).
- `python scripts/comprobar_entorno.py`: Python, dependencias y servidor MCP (7 herramientas)
  correctos; **falla solo `OPENAI_API_KEY`**; ngrok sin instalar (no hace falta hasta el día 3).
- `python -m pytest`: **6 tests pasan** (pruebas del servidor MCP, sin clave).

## 2026-11-23 — Kit descargado y documentado

- Clonado el kit: `git clone https://github.com/alamasfu10/ondo-agente.git` (commit `43dafbd`).
  Conserva su propio `.git` para recibir con `git pull` los cambios de los días 2 y 3.
- El kit no se versiona en `ebis`, pero tampoco va en `.gitignore` para que se vea en la
  búsqueda de VS Code (`git status` lo muestra como `??`; nunca se añade).
- Añadida al `AGENTS.md` del kit una sección «Arquitectura del sistema» (cambio local, sin
  commit en el repo del kit).
- Escritos `10_agentes_conversacionales/AGENTS.md` y `clase_01/explicacion-10.md`.
