# Indexación y búsqueda vectorial eficiente con LangChain y FAISS

Este directorio contiene un entorno autocontenido para ejecutar el notebook `indexacion_busqueda_vectorial_eficiente.ipynb` en Windows, macOS y Linux.

El notebook trabaja con un corpus real de AG News y compara búsqueda exacta, HNSW, IVF e IVF-PQ mediante la integración `FAISS` de LangChain. Los embeddings locales se generan con Model2Vec y no requieren claves de API, GPU, PyTorch ni cuentas en servicios externos.

## Contenido

- `indexacion_busqueda_vectorial_eficiente.ipynb`: notebook principal.
- `requirements.txt`: dependencias del entorno.
- `INICIAR_WINDOWS.cmd`: instalación y arranque en Windows.
- `INICIAR_MAC.command`: instalación y arranque en macOS.
- `INICIAR_LINUX.sh`: instalación y arranque en Linux.
- `verificar_entorno.py`: comprobación automática de Python y las librerías principales.
- `.python-version`: versión de Python utilizada: **3.11**.

## Requisitos

- Windows 10/11, macOS 12 o posterior, o una distribución Linux reciente de 64 bits.
- Conexión a Internet durante la primera ejecución.
- Aproximadamente 3 GB de espacio libre para el entorno, el dataset, el modelo y las cachés.
- No es necesario instalar Python previamente. El iniciador descarga una versión aislada de Python 3.11 mediante `uv`.

## Inicio rápido

### Windows

1. Descomprime el ZIP en una carpeta normal, por ejemplo `Documentos\busqueda_vectorial`.
2. Haz doble clic en `INICIAR_WINDOWS.cmd`.
3. Espera a que termine la instalación. JupyterLab se abrirá automáticamente.
4. Si Windows muestra una advertencia, pulsa **Más información → Ejecutar de todas formas**.

No ejecutes el archivo dentro del visor del ZIP: descomprime primero todo el contenido.

### macOS

1. Descomprime el ZIP.
2. Haz clic derecho en `INICIAR_MAC.command` y selecciona **Abrir**.
3. Confirma **Abrir** si macOS muestra una advertencia.
4. Espera a que JupyterLab se abra en el navegador.

Si el doble clic no funciona, abre Terminal, arrastra `INICIAR_MAC.command` sobre la ventana y pulsa Intro.

### Linux

Abre una terminal en la carpeta descomprimida y ejecuta:

```bash
chmod +x INICIAR_LINUX.sh
./INICIAR_LINUX.sh
```

Si el navegador no se abre, copia la dirección `http://localhost:8888` que aparezca en la terminal.

## Qué hace el iniciador

Durante el primer arranque:

1. instala `uv` si no está disponible;
2. descarga Python 3.11 sin modificar el Python global;
3. crea el entorno aislado `.venv` dentro de esta carpeta;
4. instala las dependencias compatibles;
5. comprueba el entorno;
6. abre el notebook en JupyterLab.

Los arranques posteriores reutilizan `.venv`, por lo que normalmente son mucho más rápidos.

Al ejecutar por primera vez el notebook también se descargan AG News y el modelo de embeddings. Después se reutilizan las cachés locales. La generación de embeddings se realiza por lotes y muestra progreso.

## Ejecución del notebook

En JupyterLab:

1. abre `indexacion_busqueda_vectorial_eficiente.ipynb`;
2. selecciona **Run → Run All Cells**;
3. si se solicita un kernel, elige el Python asociado a `.venv`;
4. espera a que termine cada bloque antes de interpretar los benchmarks.

El tamaño predeterminado es:

```python
MAX_DOCUMENTS = 50_000
```

Para una comprobación rápida puede cambiarse a `10_000`. Para una comparación más exigente puede elevarse hasta `120_000`; aumentarán el tiempo, la memoria y el coste de construcción.

## Instalación manual

Esta alternativa solo es necesaria si una política corporativa bloquea el iniciador.

Con `uv` disponible, abre una terminal en esta carpeta y ejecuta:

```bash
uv python install 3.11
uv venv --python 3.11
uv pip install -r requirements.txt
uv run python verificar_entorno.py
uv run jupyter lab indexacion_busqueda_vectorial_eficiente.ipynb
```

También puede usarse un Python 3.11 ya instalado:

```bash
python3.11 -m venv .venv
```

Activa después el entorno y ejecuta `python -m pip install -r requirements.txt` y `python -m jupyter lab`.

## Problemas frecuentes

### El notebook indica que Python no es 3.11

Cierra Jupyter por completo y vuelve a abrirlo usando el iniciador de esta carpeta. No lo abras desde una instalación global de Anaconda, VS Code o Jupyter salvo que selecciones expresamente el kernel de `.venv`.

### `ModuleNotFoundError` o falta alguna librería

Cierra Jupyter y vuelve a ejecutar el iniciador. Este instala cualquier dependencia que falte y ejecuta `verificar_entorno.py` antes de abrir el notebook.

### Windows no reconoce `uv` después de instalarlo

Cierra la ventana y vuelve a ejecutar `INICIAR_WINDOWS.cmd`. Si persiste, reinicia Windows para actualizar el `PATH` del usuario.

### macOS bloquea el archivo de inicio

Usa clic derecho → **Abrir**. Como alternativa, ejecuta desde Terminal:

```bash
xattr -d com.apple.quarantine INICIAR_MAC.command
chmod +x INICIAR_MAC.command
./INICIAR_MAC.command
```

### Linux muestra `Permission denied`

Ejecuta `chmod +x INICIAR_LINUX.sh` y vuelve a intentarlo. El instalador también necesita `curl`.

### La descarga del dataset o del modelo falla

Comprueba la conexión y vuelve a ejecutar la celda. Redes corporativas, proxies, VPN o antivirus pueden bloquear Hugging Face. Las descargas incompletas se reanudan o reconstruyen al volver a intentarlo.

### La generación de embeddings parece detenida

Debe aparecer una barra `Batches`. Con 50.000 documentos el tiempo depende de CPU, disco y memoria. Para una comprobación urgente, interrumpe el kernel, cambia `MAX_DOCUMENTS` a `10_000`, reinicia el kernel y ejecuta todas las celdas.

El paquete usa Model2Vec para evitar el coste elevado de `sentence-transformers` sobre CPU. No requiere PyTorch ni descarga un modelo de cientos de megabytes.

### Falta memoria o el equipo se ralentiza

Reduce `MAX_DOCUMENTS` a `25_000` o `10_000`, cierra otras aplicaciones y reinicia el kernel. Los índices y la matriz de embeddings residen principalmente en RAM durante el benchmark.

### El puerto 8888 está ocupado

Jupyter suele elegir otro puerto automáticamente. Usa la URL completa mostrada en la terminal. También puede iniciarse con:

```bash
uv run jupyter lab --port 8890 indexacion_busqueda_vectorial_eficiente.ipynb
```

## Caché y reinicio limpio

El notebook conserva descargas y embeddings para no repetir trabajo. Cambiar el modelo, el número de documentos o la semilla genera una caché distinta.

Si el entorno queda dañado, cierra Jupyter, elimina únicamente la carpeta `.venv` situada junto a este README y vuelve a ejecutar el iniciador. No hace falta borrar el notebook ni la caché del dataset.

## Versiones y compatibilidad

El entorno utiliza Python 3.11 porque dispone de paquetes precompilados compatibles de FAISS en Windows, macOS y Linux. `requirements.txt` fija las librerías sensibles y acota LangChain para evitar cambios de API incompatibles.

No se recomienda sustituir Python 3.11 por 3.12, 3.13 u otra versión sin volver a validar todo el entorno.
