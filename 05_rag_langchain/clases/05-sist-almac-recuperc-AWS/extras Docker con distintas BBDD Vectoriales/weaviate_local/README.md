# Weaviate local


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

Añade también `WEAVIATE_API_KEY` a `.env`. Genera una clave local, por ejemplo:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copia el resultado al valor `WEAVIATE_API_KEY`. Compose y el script leen la misma clave. Este usuario tiene permisos administrativos sobre el despliegue local.

## Arrancar

```bash
docker compose up -d
```
Weaviate expone HTTP en `8080` y gRPC en `50051`; el cliente Python v4 necesita ambos. Se configura autenticación API key, RBAC, acceso anónimo deshabilitado y persistencia en el volumen `weaviate_data`. No se carga un vectorizador del servidor: LangChain genera embeddings mediante OpenAI. Si cambias la clave, ejecuta `docker compose up -d --force-recreate` para aplicar la configuración.

## Verificar que está funcionando

```bash
docker compose ps
docker compose logs --tail 30 weaviate
```
Abre [readiness](http://localhost:8080/v1/.well-known/ready). Para comprobar acceso autenticado y funcionamiento completo ejecuta:
```bash
python example_weaviate_langchain.py
```

El script **recrea únicamente `S5PoliciesWeaviate`** y elimina su contenido anterior. Conserva ese nombre para el ejemplo. Ingiere tres políticas y consulta con/sin filtro. La búsqueda de la integración es híbrida; `alpha=1.0` utiliza solo el componente vectorial. Los filtros usan objetos `Filter` del SDK Weaviate. El cliente se cierra incluso si hay un error.

## Detener

```bash
docker compose down
```
El volumen persiste; `docker compose down -v` elimina los datos de este despliegue. Si falla la conexión, comprueba que ambos puertos están libres, que la clave coincide y que el servidor terminó de arrancar. Los puertos de loopback y el usuario local no constituyen un despliegue de producción.

Referencias: [Compose y autenticación](https://docs.weaviate.io/deploy/installation-guides/docker-installation), [integración LangChain](https://docs.langchain.com/oss/python/integrations/vectorstores/weaviate).
