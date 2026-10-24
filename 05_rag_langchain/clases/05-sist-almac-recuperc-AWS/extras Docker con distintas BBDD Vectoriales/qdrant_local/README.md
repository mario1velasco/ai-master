# Qdrant local


**Material adicional opcional para realizar fuera de la sesión.** Este tutorial no forma parte del notebook principal.

Docker ejecuta servicios empaquetados en contenedores. Compose lee `docker-compose.yml` y coordina su arranque. Un volumen conserva los datos aunque se detenga el contenedor. No hace falta Kubernetes ni crear imágenes.

Instala [Docker Desktop](https://docs.docker.com/desktop/) en Windows/macOS; en Windows habilita WSL 2 y contenedores Linux. En Linux instala [Docker Engine](https://docs.docker.com/engine/install/) y el [plugin Compose](https://docs.docker.com/compose/install/). Inicia Docker y verifica `docker --version` y `docker compose version`. La primera descarga requiere Internet. Los puertos se enlazan a `127.0.0.1`, para acceso únicamente desde la máquina local.

## Entorno del script

Instala Python 3.12. Abre una terminal en esta carpeta. El entorno es independiente del notebook principal.

Windows (PowerShell):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```
Si PowerShell bloquea la activación, usa `.\.venv\Scripts\python.exe` en los comandos Python posteriores.

macOS / Linux:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

Todos los sistemas:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-extra.txt
```

Edita `.env` y añade tu `OPENAI_API_KEY` con acceso a embeddings. No publiques `.env`. Las claves no se imprimen en los scripts. El corpus es ficticio; la ingesta y las consultas consumen la API de OpenAI aunque la base de datos sea local.

## Arrancar

Desde esta carpeta:
```bash
docker compose up -d
```
Qdrant expone REST en `6333` y gRPC en `6334`. El script utiliza REST y guarda los registros en el volumen `qdrant_data`. Es un despliegue local sin autenticación, limitado a loopback; no expongas estos puertos públicamente.

## Verificar que está funcionando

```bash
docker compose ps
docker compose logs --tail 30 qdrant
```
Abre [estado](http://localhost:6333/readyz) y [dashboard](http://localhost:6333/dashboard) en el navegador. El estado debe responder correctamente antes de ejecutar:
```bash
python example_qdrant_langchain.py
```

Se crea `s5_policies_qdrant` si no existe, se ingieren tres políticas y se comparan búsquedas con/sin filtro. Los IDs UUID deterministas hacen upsert en ejecuciones posteriores. El filtro usa `metadata.country` porque LangChain guarda los atributos dentro de `metadata` en el payload. La colección existente debe usar 1536 dimensiones y coseno. Los scores son los del backend, no probabilidades.

## Detener

```bash
docker compose down
```
El volumen se conserva. `docker compose down -v` elimina los datos de este despliegue; úsalo solo si quieres reiniciar el ejemplo. Si un puerto está ocupado, detén el otro servicio o cambia tanto Compose como la URL del script.

Referencias: [Qdrant y Docker](https://qdrant.tech/documentation/quickstart/), [integración LangChain](https://docs.langchain.com/oss/python/integrations/vectorstores/qdrant).
