# Milvus standalone local


**Material adicional opcional para realizar fuera de la sesión.** Este tutorial no forma parte del notebook principal.

Docker ejecuta servicios empaquetados en contenedores. Compose lee `docker-compose.yml` y coordina su arranque. Un volumen conserva los datos aunque se detenga el contenedor. No hace falta Kubernetes ni crear imágenes.

Instala [Docker Desktop](https://docs.docker.com/desktop/) en Windows/macOS; en Windows habilita WSL 2 y contenedores Linux. En Linux instala [Docker Engine](https://docs.docker.com/engine/install/) y el [plugin Compose](https://docs.docker.com/compose/install/). Inicia Docker y verifica `docker --version` y `docker compose version`. La primera descarga requiere Internet. Los puertos se enlazan a `127.0.0.1`, para acceso únicamente desde la máquina local.

Milvus standalone necesita más recursos que los otros ejemplos. Reserva al menos 4 núcleos y 8 GB de RAM para Docker y espacio libre para las imágenes y datos; consulta los requisitos oficiales según plataforma. En Windows usa Docker Desktop con WSL 2. En macOS, revisa la compatibilidad de las imágenes con tu arquitectura; si una imagen no tiene manifiesto ARM64, usa una máquina Linux x86_64 o emulación `linux/amd64` (más lenta). No requiere un despliegue cloud. La oferta gestionada asociada es **Zilliz Cloud**.

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

```bash
docker compose up -d
```
Se incluye el Compose oficial de Milvus **v3.0.1**, con los puertos del host restringidos a loopback y sin el campo obsoleto `version`. Contiene Milvus standalone, etcd (metadatos) y MinIO (objetos); Woodpecker está integrado. No es necesario descargar un archivo adicional.

Puertos: `19530` para el cliente Milvus, `9091` para estado/métricas, `9000` para MinIO y `9001` para su consola. etcd permanece en la red interna. Los directorios `volumes/etcd`, `volumes/minio` y `volumes/milvus` almacenan los datos. MinIO conserva las credenciales locales de la configuración oficial (`minioadmin`); este despliegue es exclusivamente de desarrollo y no debe exponerse a una red pública.

## Verificar que está funcionando

```bash
docker compose ps
docker compose logs --tail 30 standalone
```
Espera a que los tres servicios estén sanos; el arranque de Milvus puede tardar. Abre [healthz](http://localhost:9091/healthz), que debe responder correctamente. Después:
```bash
python example_milvus_langchain.py
```

El script **recrea únicamente `s5_policies_milvus`** mediante `drop_old=True`: descarta el contenido anterior de esa colección dedicada. Usa IDs explícitos, AUTOINDEX/coseno y consistencia Strong; ingiere tres políticas y realiza búsqueda con/sin expresión de filtro. Mantén este nombre reservado para el ejemplo. LangChain administra la colección; la sintaxis `expr` pertenece a Milvus y no es la de Pinecone.

## Detener

```bash
docker compose down
```
Los directorios de datos persisten. `down -v` no elimina los bind mounts de `volumes/`. Para reiniciar el despliegue, detén los contenedores y elimina manualmente **solo el directorio `volumes/` de esta carpeta**. Si un servicio no arranca, revisa memoria disponible, logs y puertos antes de ejecutar el script.

Referencias: [Compose oficial](https://github.com/milvus-io/milvus/releases/download/v3.0.1/milvus-standalone-docker-compose.yml), [instalación oficial](https://milvus.io/docs/install_standalone-docker-compose.md), [requisitos](https://milvus.io/docs/prerequisite-docker.md), [integración LangChain](https://docs.langchain.com/oss/python/integrations/vectorstores/milvus).
