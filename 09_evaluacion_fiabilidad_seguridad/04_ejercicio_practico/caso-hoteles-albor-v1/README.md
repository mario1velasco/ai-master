# Caso práctico · Hoteles Albor

Kit de partida del caso práctico evaluable de los Temas 8 y 9. El enunciado
completo está en el PDF que acompaña a esta carpeta.

## Puesta en marcha (10 minutos)

Usa el mismo entorno del Tema 9: Python 3.10 o superior y Ollama con `qwen2.5:7b`.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python -m albor.chat "¿Tenéis habitaciones dobles en Albor Playa para el 20 de diciembre?"
```

Si el último comando responde con la disponibilidad, todo está listo.

## Qué hay en la carpeta

```
albor/
  hotel.py          Datos simulados del sistema de reservas (huéspedes, reservas, reseñas, política)
  herramientas.py   Las herramientas que ve el agente, tal como las dejó el piloto   ← parte 1
  agente.py         El agente: bucle, trayectoria y puntos de control (no hace falta tocarlo)
  guardas.py        Guardarraíles vacíos: dejan pasar todo                            ← parte 3
  configuracion.py  Cómo se crea el agente en cada conversación                         ← parte 3
  chat.py           Prueba una pregunta y muestra la trayectoria y los efectos
pruebas/
  casos_base.json   5 casos de prueba de partida (todos normales)                        ← parte 2
  medir.py          Ejecuta los casos y calcula las métricas
logs/
  registro_produccion.jsonl   Registro de producción del 3 al 7 de noviembre             ← parte 4
```

## Comandos útiles

```bash
# Una pregunta, como huésped sin identificar o identificado en la web
python -m albor.chat "¿Puedo ir con mi perro a Albor Centro?"
python -m albor.chat --email lucia.martin@correo.com "¿Para qué fecha es mi reserva R-2041?"

# Medir: casos, repeticiones, una sola categoría y guardar el detalle en resultados/
python -m pruebas.medir
python -m pruebas.medir --casos pruebas/mis_casos.json --repeticiones 3 --guardar antes
python -m pruebas.medir --casos pruebas/mis_casos.json --categoria adversario
```

Los campos que admite un caso de prueba están explicados al principio de
`pruebas/medir.py`.

## Aviso

Todo es simulado: ningún email sale de tu ordenador y ninguna cancelación ni
reembolso es real. La fecha de hoy está fijada en el 12 de noviembre de 2026
(`HOY` en `albor/hotel.py`) para que los resultados no cambien según el día.
Con un modelo local, las respuestas varían entre ejecuciones: por eso se mide
con repeticiones.
