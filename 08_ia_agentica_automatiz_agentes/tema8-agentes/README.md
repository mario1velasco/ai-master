# Tema 8 · IA Agéntica y automatización basada en agentes

Repositorio de demos del tema. A lo largo de las seis sesiones construimos un
mismo sistema: el agente de operaciones de **Lumen Shop**, una tienda online de
cosmética. Empieza como un bucle de 80 líneas en Python y termina como un
sistema multiagente integrado en un flujo empresarial con aprobación humana.

## Antes de la primera sesión

Sigue la [guía de instalación](GUIA_INSTALACION.md). Te llevará unos 30 minutos.
En clase no se dedica tiempo a instalaciones, así que llega con el entorno listo.

## Estructura

| Carpeta | Contenido |
|---|---|
| `comun/` | Conexión con el modelo y datos simulados de la tienda |
| `sesion1/` | Del LLM al agente: agente desde cero y workflow equivalente |
| `sesion2/` | ReAct prompting, plan-and-execute, reflexión y comparativa |
| `sesion3/` | Migración a LangGraph, APIs externas, servidor MCP y aprobación humana |
| `sesion4/` | Memoria a largo plazo y checkpointing |
| `sesion5/` | Equipo multiagente con supervisor |
| `sesion6/` | El agente integrado en la empresa: webhook, API, aprobaciones e informe programado |
| `soluciones/` | Soluciones de los deberes (se publican tras la corrección en clase) |

## Cómo se ejecutan las demos

Siempre desde la carpeta raíz del repositorio y como módulo:

```bash
python -m sesion1.agente_minimo "¿Hay stock de crema hidratante?"
```

## Cambiar de modelo o de proveedor

Todo el código usa la API compatible con OpenAI. Para cambiar de modelo local
a un proveedor en la nube (o al revés) solo tienes que editar el archivo `.env`.
