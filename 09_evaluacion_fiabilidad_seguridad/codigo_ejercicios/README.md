# Tema 9 · Evaluación y control de la fiabilidad y seguridad en sistemas de agentes

Repositorio de demos y deberes del Tema 9. Usa el mismo caso del Tema 8: el
agente de atención al cliente de **Lumen Shop**, una tienda online de cosmética.
En el Tema 8 lo construimos; en este tema aprendemos a **medirlo, protegerlo y
vigilarlo** antes de dejarlo trabajar con clientes reales.

| Sesión | Tema | Demos |
|---|---|---|
| 1 | Medir al agente: métricas, pruebas y benchmarks | `sesion1/medir.py`, `sesion1/evaluar.py` |
| 2 | Fallos, guardarraíles y seguridad | `sesion2/alucinaciones.py`, `sesion2/permisos.py`, `sesion2/inyeccion.py` |
| 3 | Observabilidad, supervisión y mejora continua | `sesion3/observabilidad.py`, `sesion3/supervision.py`, `sesion3/red_teaming.py` |

Cada carpeta de sesión tiene un `README.md` con los comandos y los deberes.

## Puesta en marcha

Sigue `GUIA_INSTALACION.md`. Si ya tienes Ollama y `qwen2.5:7b` del Tema 8,
son cinco minutos:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python comprobar_entorno.py
```

## Estructura

```
comun/
  agente.py        El agente: bucle, trayectoria, guardarraíles y observador
  herramientas.py  Herramientas de la tienda, con su esquema y su riesgo
  tienda.py        Datos simulados (clientes, pedidos, reseñas, reembolsos, emails)
  evaluacion.py    Comprobaciones automáticas de un caso de prueba
sesion1/ sesion2/ sesion3/   Demos de cada sesión
```

## Un aviso sobre la seguridad

Las demos de la sesión 2 y 3 incluyen ataques (inyección de prompt, intentos
de sacar datos de otros clientes). Están pensados para aprender a defenderse y
todo es simulado: los emails solo se guardan en una lista y los reembolsos no
son reales. Pruébalos solo sobre tus propios agentes.
