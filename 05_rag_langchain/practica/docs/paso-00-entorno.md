# Paso 0 · Entorno

> Deja listo el entorno para trabajar: `.env` de la práctica, el PDF en `data/` y los lanzadores. No toca el notebook.

## Qué hemos hecho

1. **`practica/Recursos /.env`** (ignorado por git, nunca se entrega) con la clave del sandbox de EBIS y `OPENAI_CHAT_MODEL=gpt-5-nano`. **Nunca se copia a ficheros versionados.**
2. **`practica/Recursos /data/TENERIFE.pdf`**: copia del PDF (el notebook exige esa ruta; `data/` está ignorado por git).
3. **`scripts/practica.sh`**: abre JupyterLab con el `.venv` común **sin exportar el `.env` raíz**, para que `OPENAI_API_KEY` sea la de la práctica y no la personal.
4. **`practica/verificar.sh`** y `practica/tests/`: ejecutan los tests hasta el paso N, sin red y sin coste.

## Cómo ejecutarlo

```bash
scripts/practica.sh            # JupyterLab en practica/Recursos con la clave de la práctica
practica/verificar.sh 0        # tests del paso 0
```
En VS Code: kernel **.venv (Python 3.11)** o **Python (rag-curso)**; el notebook lee `Recursos /.env` porque su carpeta de trabajo es `Recursos `.

## En qué clase nos fijamos

- [Raíz `CLAUDE.md` §4 (entorno común y política de `.env`)](../../CLAUDE.md)
- [Sesión 5 · §4 Entorno y configuración del notebook (`.env`, claves, `remote_operation`)](../../clases/05-sist-almac-recuperc-AWS/EXPLICACION_sesion_05.md)

## Celda(s) del notebook rellenadas

Ninguna.
Notebook: [rag_tenerife.ipynb](../Recursos%20/rag_tenerife.ipynb)

## Resultado esperado

5 tests OK: PDF en `data/`, entregables presentes, imports, `.env` con `gpt-5-nano` (solo nombres) y notebook válido.

## Commit sugerido

- **Mensaje:** `Añade entorno de la práctica: verificar.sh, tests base y lanzador practica.sh`
- **Ficheros:** `scripts/practica.sh`, `practica/verificar.sh`, `practica/tests/__init__.py`, `practica/tests/ayudas.py`, `practica/tests/test_paso_00_entorno.py`
