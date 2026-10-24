# Caso práctico RAG Tenerife

Lee el enunciado y la rúbrica. El notebook contiene cuatro funciones por completar; las utilidades de carga y registro ya están implementadas.

## Preparación antes de la actividad

Python 3.11 o 3.12, conexión y acceso al modelo preparado por el profesorado. Desde esta carpeta:

```bash
python -m venv .venv
```

Activa `.venv` (`source .venv/bin/activate` en macOS/Linux o `.venv\Scripts\Activate.ps1` en PowerShell), y ejecuta:

```bash
python -m pip install -r requirements.txt
python -m ipykernel install --user --name rag-tenerife --display-name "Python RAG Tenerife"
python -m jupyterlab
```

Selecciona el kernel **Python RAG Tenerife**. Copia `.env.example` a `.env` y configura tu clave local. No entregues `.env`. El chat y los embeddings son configurables: `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`. Los nombres incluidos son una configuración inicial que el profesorado debe comprobar con su cuenta. Si el modelo de chat elegido no admite `temperature`, ajusta su construcción.

Las llamadas de la sección 4 en adelante usan servicios externos y pueden consumir saldo. No se necesitan Pinecone, despliegue ni una interfaz web. Se admite otro proveedor preparado por el profesorado manteniendo los requisitos y documentando el cambio.

## Ejecución

1. Abre el notebook desde esta carpeta y comprueba que existe `data/TENERIFE.pdf`.
2. Completa las cuatro funciones y justifica los parámetros.
3. Ejecuta desde un kernel limpio; se crea un índice y se compara k = 2 con k = 4.
4. Revisa las 12 salidas en `resultados.json` y completa `revision.csv`. Un 0 indica fallo, un 1 cumplimiento; `NA` no aplica. Las celdas vacías son pendientes, no ceros.
5. Ejecuta el resumen y redacta la conclusión del notebook.

El guardado conserva `revision.csv` si ya existe para no borrar tu revisión. Al repetir llamadas, guarda una copia de los archivos anteriores y revisa que las filas se refieran a las respuestas nuevas. No presentes resultados de una prueba anterior como si fueran de la nueva configuración.

## Problemas habituales

- `FileNotFoundError`: abre Jupyter desde la carpeta del notebook y coloca la guía en `data/TENERIFE.pdf`.
- Clave ausente: configura `.env`; no pegues la clave en el notebook.
- Acceso denegado o modelo inexistente: confirma el identificador habilitado para la clase.
- Cuota o conexión: resuelve el error y repite; una llamada fallida no es una abstención correcta.
- Importación fallida: comprueba que has seleccionado el kernel del entorno instalado.

## Entrega

Un ZIP con el notebook ejecutado, resultados.json, revision.csv, README.md, requirements.txt, preguntas.csv y utilidades.py (más cualquier módulo que hayas añadido). No incluyas claves, `.env`, `.venv` ni cachés. El corrector aporta la misma guía en `data/TENERIFE.pdf`.
