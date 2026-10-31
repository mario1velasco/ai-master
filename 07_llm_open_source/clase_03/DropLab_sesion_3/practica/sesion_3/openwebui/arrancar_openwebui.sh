#!/usr/bin/env bash
# Arranca Open WebUI (Docker, ARM64) para la sesión 3, con la configuración comprobada en el Jetson.
#
#   bash practica/sesion_3/openwebui/arrancar_openwebui.sh          # arrancar (o reiniciar si ya existe)
#   bash practica/sesion_3/openwebui/arrancar_openwebui.sh parar
#   bash practica/sesion_3/openwebui/arrancar_openwebui.sh borrar   # borra también sus datos (chats, Pipe)
#
# Decisiones (docs/sesion_3/02):
#   --network=host     el contenedor ve Ollama (127.0.0.1:11434) y nuestra API (127.0.0.1:8000) como si estuviera
#                      fuera. Sin esto, «127.0.0.1» dentro del contenedor sería el propio contenedor.
#   PORT=3000          la interfaz, en http://<jetson>:3000
#   WEBUI_AUTH=False   un solo usuario (el profesor) y sin contraseñas: SOLO para el aula. No usar en una red abierta.
#   Sin RAG propio     el RAG es el de la sesión 2 (vía la API). No se suben documentos a Open WebUI.
#   Imagen fija        ghcr.io/open-webui/open-webui:main se probó como v0.12.0 (10/10/2026). Para fijarla:
#                      OPENWEBUI_IMAGEN=ghcr.io/open-webui/open-webui:v0.12.0 bash arrancar_openwebui.sh
#
# Licencia: Open WebUI License (BSD-3 + cláusula de marca: no quitar «Open WebUI» con más de 50 usuarios en 30 días).
set -euo pipefail
NOMBRE=droplab-webui
IMAGEN="${OPENWEBUI_IMAGEN:-ghcr.io/open-webui/open-webui:main}"

case "${1:-arrancar}" in
  parar)  docker stop "$NOMBRE" && echo "Parado." ; exit 0 ;;
  borrar) docker rm -f "$NOMBRE" 2>/dev/null; docker volume rm droplab-webui 2>/dev/null; echo "Borrado (contenedor y datos)."; exit 0 ;;
esac

if docker ps -a --format '{{.Names}}' | grep -qx "$NOMBRE"; then
  echo "Ya existe: reiniciando…"; docker restart "$NOMBRE" >/dev/null
else
  docker run -d --name "$NOMBRE" --network=host --restart unless-stopped \
    -e PORT=3000 \
    -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \
    -e WEBUI_AUTH=False \
    -e WEBUI_NAME="DropLab" \
    -e ENABLE_OPENAI_API=False \
    -e ENABLE_TITLE_GENERATION=False -e ENABLE_TAGS_GENERATION=False -e ENABLE_FOLLOW_UP_GENERATION=False \
    -e ANONYMIZED_TELEMETRY=False -e DO_NOT_TRACK=true -e SCARF_NO_ANALYTICS=true \
    -v droplab-webui:/app/backend/data \
    "$IMAGEN" >/dev/null
fi
echo -n "Esperando a Open WebUI"
for _ in $(seq 1 90); do
  if curl -fs -m 2 http://127.0.0.1:3000/health >/dev/null; then echo " ✓"; break; fi
  echo -n "."; sleep 2
done
curl -s http://127.0.0.1:3000/api/config | python3 -c "import json,sys; d=json.load(sys.stdin); print('Open WebUI', d['version'], '· http://127.0.0.1:3000')"
echo "Siguiente: python practica/sesion_3/openwebui/instalar_pipe.py   (instala «DropLab Analista»)"
