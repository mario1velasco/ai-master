# Travel Agency

Agente de **Viajes Nimbo** (agencia ficticia) que responde preguntas consultando la base de datos (text-to-SQL
sobre DuckDB) o la documentación (RAG con búsqueda híbrida), con modelos open source en local y una API FastAPI.

- Diseño: [`PROYECTO.md`](PROYECTO.md)
- Instrucciones para agentes de IA: [`AGENTS.md`](AGENTS.md)

## Puesta en marcha

```bash
uv sync
uv run pytest
```

Requisitos: [uv](https://docs.astral.sh/uv/) y, a partir de la fase 5, [Ollama](https://ollama.com) con `qwen3:4b-instruct`.
