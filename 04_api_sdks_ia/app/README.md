# `app` — arquitectura del backend

## Arquitectura: `main` → `services` → `api_clients`

Cada funcionalidad de este backend atraviesa tres capas, cada una con una única
responsabilidad:

```
main.py  ──▶  services/  ──▶  api_clients/  ──▶  proveedor externo (Anthropic...)
(rutas)       (lógica de      (llamadas HTTP a
               negocio)        APIs externas)
```

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Entrada | `main.py` | Define los endpoints, valida la request (Pydantic), llama al `service` correspondiente y convierte el resultado en una respuesta HTTP |
| Negocio | `services/` | Decide *qué* hacer y en qué orden; combina datos de uno o varios `api_clients` (aquí: rotación de API keys ante saturación) |
| Integración | `api_clients/` | Sabe hablar con *un* proveedor externo: construye la request, autentica y parsea la respuesta |

El objetivo de esta separación: si cambias de proveedor (por ejemplo, otro LLM), solo
tocas el módulo correspondiente en `api_clients/` — `main.py` y `services/` no saben ni
les importa qué proveedor hay detrás de la interfaz.

## Carpetas

- `config.py` — único punto donde se leen variables de entorno.
- `services/` — lógica de negocio (`chat_service.py`: rotación de keys ante 429/529).
- `api_clients/` — integración con proveedores externos (`anthropic_client.py`).
- `scripts/` — tareas puntuales, ejecutables a mano o por cron (`check_keys.py`).
- `utils/` — código transversal reutilizable (`logger.py`).
