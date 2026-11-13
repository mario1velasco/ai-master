# Guía de instalación · Trabajo previo a la sesión 1

Tiempo estimado: 10 minutos si conservas el entorno del Tema 8; 30 minutos si
empiezas de cero. Al terminar, el script de comprobación debe mostrar todo en verde.

## 1. Requisitos

- Python 3.10 o superior (`python3 --version`).
- Un modelo de lenguaje con *tool calling*:
  - **Opción A (recomendada):** Ollama con `qwen2.5:7b`, el mismo del Tema 8.
    Necesita unos 6 GB libres en disco y 8 GB de RAM.
  - **Opción B:** un proveedor en la nube compatible con la API de OpenAI.

## 2. Descarga el repositorio

Descarga `tema9-fiabilidad.zip` del campus y descomprímelo. Abre una terminal
dentro de la carpeta `tema9-fiabilidad`.

## 3. Crea el entorno e instala las dependencias

```bash
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Verás `(.venv)` al principio de la línea. Actívalo cada vez que abras una terminal nueva.

## 4. El modelo

**Opción A.** Si ya tienes Ollama del Tema 8, ábrelo y comprueba con
`ollama list` que está `qwen2.5:7b`. Si no, instálalo desde
[ollama.com/download](https://ollama.com/download) y descarga el modelo:

```bash
ollama pull qwen2.5:7b
```

**Opción B.** No instales Ollama: en el paso 5 rellena la URL, la clave y el
modelo de tu proveedor. No compartas nunca tu clave.

## 5. Configura el archivo `.env`

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Con la opción A no hay que cambiar nada.

## 6. Comprueba que todo funciona

```bash
python comprobar_entorno.py
```

Debe terminar con «Todo listo para el Tema 9». Opcionalmente, comprueba
también las pruebas automáticas (no necesitan el modelo):

```bash
python -m pytest -q
```

## 7. Opcional para la sesión 3: MLflow

La demo de observabilidad puede registrar las trazas en MLflow (lo usamos en el
material complementario del Tema 8):

```bash
pip install "mlflow>=3.8"
```

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| `No se puede conectar con el modelo` | Abre Ollama y comprueba con `ollama list` que está el modelo |
| `model not found` | El nombre de `.env` no coincide con `ollama list` |
| `ModuleNotFoundError` | El entorno no está activado: `source .venv/bin/activate` |
| `pip` no encuentra paquetes (red de empresa) | `PIP_CONFIG_FILE=/dev/null pip install --index-url https://pypi.org/simple -r requirements.txt` |
| `no space left on device` al descargar el modelo | Libera espacio o usa `qwen2.5:3b` y cámbialo en `.env` |
