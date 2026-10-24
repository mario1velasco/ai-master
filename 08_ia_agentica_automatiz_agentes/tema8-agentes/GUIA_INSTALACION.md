# Guía de instalación · Trabajo previo a la sesión 1

Tiempo estimado: 30 minutos. Al terminar, el script de comprobación debe mostrar
todo en verde. Si algo falla, revisa la sección de problemas frecuentes al final.

## 1. Requisitos

- Python 3.10 o superior.
- Unos 6 GB libres en disco y 8 GB de RAM para el modelo local. Si tu equipo no
  llega, usa la opción B del paso 5.

## 2. Descarga el repositorio

Descarga la carpeta del tema desde el campus y descomprímela, o clónala con Git
si se te ha facilitado la URL.

## 3. Crea un entorno virtual e instala las dependencias

Abre una terminal en la carpeta del repositorio:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 4. Instala Ollama y descarga el modelo

1. Descarga Ollama desde [ollama.com](https://ollama.com) e instálalo (ya lo usaste en el Tema 7).
2. Descarga el modelo de las demos:

```bash
ollama pull qwen2.5:7b
```

Para la sesión 4 (memoria) descarga también un modelo de embeddings. Es opcional:
si no lo tienes, el código usa una alternativa local más sencilla.

```bash
ollama pull nomic-embed-text
```

Si tu equipo va justo de memoria, usa una versión más ligera (`qwen2.5:3b`) y
cámbiala en el `.env`. Funcionará peor en tareas largas, pero sirve para seguir
las sesiones.

## 5. Configura el archivo `.env`

Copia `.env.example` como `.env`.

- **Opción A, modelo local (recomendada):** no tienes que cambiar nada.
- **Opción B, proveedor en la nube:** si no puedes ejecutar el modelo local,
  crea una cuenta gratuita en un proveedor compatible con la API de OpenAI
  (el `.env.example` incluye Groq como ejemplo), y rellena la URL, la clave y
  el nombre del modelo. No compartas nunca tu clave.

## 6. Comprueba que todo funciona

```bash
python comprobar_entorno.py
```

Debe terminar con «Todo listo para el Tema 8».

## Lectura previa

*Building effective agents* (Anthropic). Fíjate sobre todo en la diferencia entre
*workflows* y agentes: es el punto de partida de la primera sesión.

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| `No se puede conectar con el modelo` | Abre la aplicación de Ollama y comprueba que `ollama list` muestra el modelo |
| `model not found` | El nombre en `.env` no coincide con el modelo descargado. Revisa `ollama list` |
| `El modelo no ha usado la herramienta` | El modelo no soporta tool calling. Usa uno de los recomendados |
| Respuestas muy lentas | Usa el modelo de 3B o la opción B |
| `ModuleNotFoundError: comun` | Ejecuta los scripts desde la carpeta raíz del repositorio |
