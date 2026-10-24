# Configuración del entorno

Ejecuta los comandos desde la carpeta que contiene `requirements.txt`. Se utiliza **uv** para gestionar Python y crear `.venv` con la versión compatible. No necesitas tener Python instalado ni modificar el Python del sistema.

## 1. Instalar uv

Si ya tienes uv, omite este paso.

**Windows — PowerShell**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux — terminal**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Cierra y vuelve a abrir la terminal después de instalarlo. [Instalación oficial de uv](https://docs.astral.sh/uv/getting-started/installation/).

## 2. Crear el entorno e instalar dependencias

**Todos los sistemas**
```bash
uv venv --managed-python --python 3.12 .venv
uv pip install -r requirements.txt
```

uv descarga automáticamente un Python gestionado si es necesario y lo utiliza para `.venv`. Las dependencias se instalan en ese entorno. [Gestión de entornos](https://docs.astral.sh/uv/pip/environments/).

## 3. Configurar las variables

**Windows — PowerShell**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

Edita `.env` y configura:

- `OPENAI_API_KEY`: clave con acceso a embeddings y facturación habilitada.
- `PINECONE_API_KEY`: clave del proyecto con permiso para crear o acceder al índice.
- `PINECONE_INDEX_NAME` (opcional): nombre del índice; 1–45 caracteres en minúsculas, números o guiones, con extremos alfanuméricos.
- `PINECONE_CLOUD` y `PINECONE_REGION` (opcionales): ubicación admitida por tu plan.

No compartas el archivo `.env`.

## 4. Lanzar JupyterLab desde el entorno

No es necesario activar el entorno: estos comandos utilizan directamente su Python.

**Windows — PowerShell**
```powershell
.\.venv\Scripts\python.exe -m jupyterlab
```

**macOS / Linux**
```bash
./.venv/bin/python -m jupyterlab
```
