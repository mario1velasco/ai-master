# TRAVEL-001 · Generar un conjunto de datos sintéticos grande y reproducible

| Campo | Valor |
|---|---|
| Tipo | Story |
| Carpeta del proyecto | `travel-agency/` (`database/`) |
| Estado | Borrador, pendiente de revisión |
| Creado | 2026-11-07 |
| Etiquetas | database, datos, seed, fase-2b |

## Historia de usuario

**Como** desarrollador de Viajes Nimbo, **quiero** un generador con semilla fija que amplíe los CSV escritos a mano
hasta miles de filas coherentes, **para que** el text-to-SQL, su dataset de evaluación y el agente trabajen con un
volumen realista sin perder los casos ancla ni las trampas que ya conocemos.

## Contexto

La fase 2a dejó 8 CSV con ~70 filas a mano en `database/data/` y la capa semántica (`semantic_layer.py`) con
`CHECKS` calculados a mano sobre esas filas. `PROYECTO.md` §3 pide después un generador con **semilla fija** que
amplíe a muchas filas conservando las filas a mano. Algunos `CHECKS` son cifras globales (7 reservas, neto
1.849 €, dos «Ana López») que dejarían de cuadrar si se mezclan filas generadas: por eso el conjunto generado va
en una carpeta aparte y `data/` sigue siendo la base exacta de los tests. `open_db(data_dir)` ya admite otra carpeta.

**Referencias leídas:** `travel-agency/PROYECTO.md` §3 y §10, `travel-agency/AGENTS.md` (fila 2),
`database/AGENTS.md`, `database/src/database/semantic_layer.py` (`open_db`, `CHECKS`),
`database/tests/{conftest.py, test_database_audit.py, test_database_semantic_layer.py}`, `database/data/*.csv`,
`telemetry/AGENTS.md` (`span()`), `07_llm_open_source/clase_01/Ejercicios/DropLab/datos/` (volumen y estilo de
trampas: ~1.400 ventas), `08_ia_agentica_automatiz_agentes/tema8-agentes/comun/tienda.py` (datos fijos y
reproducibles).

**Desvíos respecto al patrón de clase:**
- **La fase no tiene referencia en el repo**: en clase los datos ya venían hechos (DropLab) o fijos en código
  (`tienda.py`); nadie escribe un generador. El enfoque lo decidió Mario el 2026-11-07.
- **Sin Faker** (decisión de Mario): listas de nombres y apellidos escritas a mano + `random` de la biblioteca
  estándar con semilla. `PROYECTO.md` §3 decía Faker: se actualiza.
- **Conjunto generado en carpeta aparte** (`database/data_generated/`, subido a git) en lugar de ampliar `data/`.
- Script en inglés (`generate.py` y no `generar.py`, como dice `PROYECTO.md`), por la regla de código en inglés.

## Alcance

**Dentro**
- Un comando que, a partir de `data/` y una semilla, escribe los 8 CSV en `data_generated/`: filas a mano
  intactas + filas generadas.
- Unos 12 aeropuertos reales más, escritos a mano en `data/aeropuertos.csv` (coordenadas y zona IANA reales).
- Coherencia del negocio en las filas generadas: horas y zonas, estados, itinerarios, fechas, pagos y
  compensaciones del Reglamento 261/2004.
- Tests: auditoría y `CHECKS` por id sobre el conjunto generado, reproducibilidad y errores del comando.
- Un evento de telemetría por ejecución.

**Fuera**
- Que text2sql o el agente usen el conjunto generado (fase 5 y siguientes).
- Cambiar las vistas, `COMMENTS`, `GUIDE` o los `CHECKS` actuales.
- Aerolíneas nuevas (se quedan las 6 actuales).
- Contrato de métricas nuevo en `contracts/`.

## Criterios de aceptación

### Camino feliz

**AC-1 — Se genera el conjunto grande**
- **Dado** `data/` con sus 8 CSV a mano
- **Cuando** se ejecuta el generador con la semilla por defecto
- **Entonces** `data_generated/` contiene los 8 CSV con las mismas columnas y en el mismo orden que en `data/`
- **Y** hay al menos 1.000 clientes, 2.000 vuelos y 3.000 reservas

**AC-2 — Las filas a mano siguen intactas**
- **Dado** el conjunto generado
- **Cuando** se compara cada CSV de `data/` con su CSV de `data_generated/`
- **Entonces** cada fila de `data/` aparece idéntica, valor por valor, en `data_generated/`

**AC-3 — La auditoría de integridad pasa sobre el conjunto generado**
- **Dado** el conjunto generado abierto con la capa semántica
- **Cuando** se pasa la auditoría (claves únicas, referencias entre tablas, incidencia en un vuelo de su
  reserva, toda reserva con tramos, signo de los pagos, cobrado = `importe_total`)
- **Entonces** ninguna comprobación encuentra filas que la incumplan

**AC-4 — Los CHECKS que miran un id dan las mismas cifras**
- **Dado** el conjunto generado abierto con la capa semántica
- **Cuando** se ejecutan los `CHECKS` de R-1042, IB3166 (retrasos, duración, distancia y hora local), VY1234,
  FR7312, IB0731/AF1001, R-1044, R-1043, I-03 y C-007
- **Entonces** dan exactamente las cifras de `data/` (p. ej. R-1042: 1.250 € cobrado y 1.100 € neto; IB3166:
  297, 312, 510 min y 5.762 km)

### Casos límite

**AC-5 — Ningún código de vuelo se repite**
- **Dado** el conjunto generado
- **Cuando** se cuentan los vuelos por `codigo_vuelo`
- **Entonces** cada código aparece una sola vez en todo el conjunto, incluidos los de las filas a mano
  (IB3166, VY1234, FR7312, IB0731, AF1001…)

**AC-6 — El desfase horario es el de la zona del aeropuerto en esa fecha**
- **Dado** el conjunto generado
- **Cuando** se compara el desfase de cada hora de salida y de llegada con el de la `zona_horaria` de su
  aeropuerto en ese instante
- **Entonces** coinciden siempre, también con el cambio de hora (p. ej. Madrid: +02:00 en julio, +01:00 en diciembre)
- **Y** la llegada prevista es siempre posterior a la salida prevista

**AC-7 — Los vuelos posteriores a la fecha de corte están programados**
- **Dado** la fecha de corte fija 2026-11-01
- **Cuando** se miran los vuelos generados
- **Entonces** los que salen después de esa fecha están en `programado` y sin `salida_real` ni `llegada_real`
- **Y** ningún vuelo que sale antes está en `programado`

**AC-8 — El estado del vuelo cuadra con sus horas**
- **Dado** el conjunto generado
- **Cuando** se mira el estado de cada vuelo y su retraso a la llegada
- **Entonces** los `cancelado` no tienen horas reales, los `en_hora` llegan con 15 min de retraso o menos y los
  `retrasado` con más de 15 min

**AC-9 — Los itinerarios encadenan**
- **Dado** las reservas generadas con escala o con ida y vuelta
- **Cuando** se recorren sus tramos por `orden`
- **Entonces** en un mismo trayecto cada tramo sale del aeropuerto al que llegó el anterior y después de su llegada prevista
- **Y** la vuelta sale del destino final de la ida, después de que la ida llegue

**AC-10 — El orden de las fechas cuadra**
- **Dado** el conjunto generado
- **Cuando** se comparan las fechas de cada cliente, reserva, tramo y pago
- **Entonces** `fecha_alta` del cliente ≤ `fecha_reserva` ≤ salida prevista del primer tramo
- **Y** ningún pago es anterior a la `fecha_reserva` de su reserva

**AC-11 — Los pagos cuadran con el estado de la reserva**
- **Dado** el conjunto generado
- **Cuando** se agregan los pagos por reserva
- **Entonces** toda reserva `cancelada` tiene al menos un reembolso
- **Y** ninguna reserva tiene importe neto negativo

**AC-12 — La compensación sigue el Reglamento 261/2004**
- **Dado** las incidencias generadas, con la distancia y el retraso en destino final **del viaje**
- **Cuando** se mira su `estado` y su `compensacion`
- **Entonces** las de retraso ≥ 180 min o de cancelación que están `resuelta` llevan 250 € (hasta 1.500 km),
  400 € (más de 1.500 km dentro de la UE, o de 1.500 a 3.500 km) o 600 € (el resto)
- **Y** las de retraso de menos de 180 min están `rechazada` y sin importe, y las de equipaje y las `abierta`
  no tienen importe

**AC-13 — Las trampas siguen en las filas generadas**
- **Dado** el conjunto generado, sin contar las filas a mano
- **Cuando** se buscan los casos difíciles de `PROYECTO.md` §3
- **Entonces** hay al menos uno de cada: dos clientes con el mismo nombre y apellidos, cliente sin reservas,
  reserva con escala, ida y vuelta, reembolso parcial, cancelación con reembolso total, vuelo que llega pasada
  la medianoche por el retraso, vuelo programado y vuelo cancelado

### Errores

**AC-14 — Una semilla que no es un número entero da un error de uso**
- **Dado** un `data_generated/` ya generado
- **Cuando** se ejecuta el generador con `--seed abc`
- **Entonces** el comando termina con un error de uso que explica que la semilla debe ser un número entero
- **Y** los archivos de `data_generated/` no cambian

**AC-15 — Si falta un CSV a mano, el error lo nombra**
- **Dado** una carpeta de origen sin `vuelos.csv`
- **Cuando** se ejecuta el generador sobre ella
- **Entonces** el comando termina con un error que nombra `vuelos.csv`
- **Y** no se escribe ningún CSV a medias en la carpeta de salida

### No funcionales

**AC-16 — Misma semilla, mismos bytes**
- **Dado** el conjunto subido a git en `data_generated/`
- **Cuando** se regenera dos veces con la semilla por defecto en una carpeta temporal
- **Entonces** los dos resultados son idénticos byte a byte entre sí y con los CSV subidos

**AC-17 — Otra semilla da otros datos**
- **Dado** el generador
- **Cuando** se ejecuta con la semilla 42 y, aparte, con la 7
- **Entonces** las filas generadas son distintas
- **Y** las filas a mano son las mismas en los dos

**AC-18 — Cada ejecución deja un evento de telemetría**
- **Dado** la telemetría apuntando a una carpeta temporal
- **Cuando** se ejecuta el generador con la semilla 42
- **Entonces** se escribe un evento `database.seed` del componente `database` con `status = ok`
- **Y** el evento incluye la semilla y el número de filas por tabla

**AC-19 — Lo que ya existe no se rompe**
- **Dado** el cambio terminado
- **Cuando** se ejecutan los tests actuales de `database/` sobre `data/`
- **Entonces** pasan todos con sus cifras exactas (7 reservas, neto 1.849 €, join directo 3.543 €…)
- **Y** de `data/` solo ha cambiado `aeropuertos.csv`, con filas nuevas al final y las 8 actuales sin tocar

## Definición de hecho

- [ ] Cada AC cubierto por un test automático que pasa
- [ ] Toda la suite del proyecto en verde (`uv run pytest`)
- [ ] ruff y ty limpios
- [ ] `database/AGENTS.md` y `README.md` actualizados (comando, `data_generated/`, sin Faker); fila 2 de
      `travel-agency/AGENTS.md` con el estado, en qué se fijó y los desvíos; `PROYECTO.md` §3 sin Faker
- [ ] Commits sin atribución a la IA

## Supuestos y preguntas abiertas

**Supuestos**
- Semilla por defecto: 42.
- Umbral de `en_hora`: hasta 15 min de retraso a la llegada; las filas a mano lo cumplen (KL1701 +10, FR7311 +11).
- Vuelos entre 2025-01-01 y 2027-03-31; corte en 2026-11-01 (decidido por Mario).
- Reglamento 261 simplificado: sin la reducción del 50 % del art. 7.2 ni circunstancias extraordinarias; la
  cancelación compensa según la distancia, sin mirar el preaviso. Las filas a mano ya cuadran con esta regla
  (I-01: 600 €, I-02: rechazada con 175 min, I-04: 250 €).
- Emails en `@example.com`, todo en EUR, `nivel_fidelidad` y estados con un reparto razonable (sin AC).
- Número de incidencias: el que salga de los vuelos retrasados y cancelados (sin mínimo en AC).
- Los aeropuertos nuevos los elige quien desarrolle, con datos reales comprobados.

**Preguntas abiertas**
- `schema()` tarda hoy ~4 s sobre `data/`: medir cuánto tarda con el conjunto grande y decidir si hace falta un
  límite antes de la fase 5.
- ¿Qué conjunto abre `open_db()` por defecto cuando llegue text2sql (fase 5)? Hoy `data/`; no se cambia en este ticket.
