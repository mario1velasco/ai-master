# Configuración del entorno

Se recomienda Python 3.11 o 3.12.

## 1. Crear el entorno virtual

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## 2. Instalar las dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Registrar el kernel

```bash
python -m ipykernel install --user --name recuperacion-informacion --display-name "Python (recuperación de información)"
```

## 4. Configurar la API opcional de OpenAI

El notebook funciona sin claves mediante modelos locales. Para utilizar embeddings de OpenAI, defina `OPENAI_API_KEY` antes de iniciar Jupyter.

### Windows (PowerShell)

```powershell
$env:OPENAI_API_KEY="su_clave"
```

### macOS y Linux

```bash
export OPENAI_API_KEY="su_clave"
```

## 5. Iniciar Jupyter

```bash
jupyter lab
```

Abra `metodos_modernos_recuperacion.ipynb` y seleccione el kernel **Python (recuperación de información)**. La primera ejecución con los modelos locales descarga sus pesos y los conserva en la caché del sistema.
