## 1.

### 1.1 Mi equipo y el modelo elegido
- **Sistema:** Ubuntu 26.04.1 LTS
- **RAM:** 16 GB 
- **Disco libre:** 732 GB (de 937 GB)
- **GPU:** NVIDIA GeForce GTX 1650 Mobile / Max-Q con 4 GB de VRAM
- **CPU:** Intel Core i7-10750H / 2.60 GHz (4 núcleos, 8 núcleos)

Elijo qwen3:4b-instruct porque es el modelo de clase y en https://www.canirun.ai/model/qwen3-vl-4b me dice que corre bien.


== Ventas netas por tienda ==
Goya       MAD-GOY: bruto 33.000,00 € -> 31.000,00 € | abonos 1.000,00 € -> 1.000,00 € | neto 32.000,00 € -> 30.000,00 € (-2.000,00 €, -6,2 %)
Malasaña   MAD-MAL: bruto 42.000,00 € -> 28.000,00 € | abonos 2.000,00 € -> 2.000,00 € | neto 40.000,00 € -> 26.000,00 € (-14.000,00 €, -35,0 %)

(.venv) ➜  07_llm_open_source git:(master) ollama run qwen3:4b-instruct "¿Cuánto cayeron las ventas netas de la tienda de Malasaña de DropLab entre marzo y abril de 2026?"

No hay datos disponibles sobre las ventas netas de la tienda de Malasaña de DropLab entre marzo y abril de 2026. Este período aún no ha ocurrido (actualmente estamos en 2024), por lo que no es posible proporcionar 
información sobre ventas futuras.

Además, no existe información pública o registrada de una tienda específica de Malasaña perteneciente a DropLab, ni de sus ventas netas en ese periodo.

Si estás buscando información sobre ventas de una tienda específica, es posible que haya un error en el nombre, la fecha o el nombre de la empresa. Si me das más contexto o datos, puedo ayudarte mejor.

¿Te refieres a una tienda real, o es una pregunta hipotética o de ficción?

(.venv) ➜  07_llm_open_source git:(master) ollama ps                                                                                                                       
NAME                 ID              SIZE      PROCESSOR          CONTEXT    UNTIL              
qwen3:4b-instruct    0edcdef34593    3.2 GB    67%/33% CPU/GPU    4096       4 minutes from now   
- **SIZE (3,2 GB)**: la memoria que ocupa el modelo **mientras está cargado**. Es más que los 2,5 GB que ocupa la descarga, porque además de los pesos del modelo hay que reservar memoria para el contexto (la conversación que tiene delante). 
- **PROCESSOR (67 % CPU / 33 % GPU)**: el modelo no cabe entero en mi tarjeta gráfica. El resto lo ejecuta el procesador con la RAM normal. Por eso irá más lento que si estuviera todo en la GPU.
- **CONTEXT (4096)**: el tamaño de la ventana de contexto, es decir, cuántos tokens puede tener delante a la vez (instrucciones + datos + su respuesta). Esta ventana se reserva en memoria por adelantado: cuanto más grande, más SIZE.

### 1.4 Pruebas 1 y 4 del script 04 frente al Jetson

| | Tiempo total | Carga del modelo | Tokens entrada → salida | Tokens/s |
|---|---|---|---|---|
| Prueba 1 (sin datos, sin reglas) | 19,0 s | 6,9 s | 73 → 127 | 11,6 |
| Prueba 4 (hechos + reglas) | 34,0 s | 0,6 s | 1.436 → 197 | 8,6 |
| Jetson del aula | ~25 s | — | — | ~8 |

### 1.5 Frase prueba 4 --modo sin-datos
Además, se observa una caída del 18% en compras de productos de alta gama. 
Con : Reglas: sí · Correo de dirección: sí · Hechos calculados: sí
Me sale todo correcto

## 2

### SQL
B-BCN-EIX-1228,B-BCN-EIX-ORD-0013,2026-04-12,BCN-EIX,DAILY_TEE_BLANCO_L,2,32.00,8.10,55.90,completada
B-BCN-EIX-1229,B-BCN-EIX-ORD-0013,2026-04-12,BCN-EIX,STREET_ONE_ARENA_40,2,95.00,24.07,165.93,completada
linea_id,fecha_venta,cantidad,importe_linea,reembolso_id,fecha_reconocimiento,importe_reembolso
B-BCN-EIX-1228,2026-04-12,2,55.90,,,
B-BCN-EIX-1229,2026-04-12,2,165.93,,,
| Dato | Valor |
|---|---|
| Tienda | BCN-EIX (Eixample) |
| Líneas | 2 (B-BCN-EIX-1228 y B-BCN-EIX-1229) |
| Unidades | 4 (2 + 2) |
| Importe total | 221,83 € (55,90 + 165,93) |
| Fecha | 12/04/2026 → **periodo B** (30 mar – 26 abr) |
| Reembolsos | **Ninguno** |

### Hechos calculados
### 2.2 Borradores A, B, C y D

Tipos de error: 1 cifra inventada · 2 cifra real, significado falso · 3 afirmación ajena como dato ·
4 causa no demostrada · 5 interpretación contradicha.

#### Borrador A → Con cambios

| Frase | Tipo | Por qué |
|---|---|---|
| «afectó a 8 SKUs, principalmente en el modelo Street One» | 2 | El 8 son los SKU observados, no los afectados: sin stock hubo 4. «Principalmente» sugiere otros modelos, pero solo se observa Street One. |

#### Borrador B → No

| Frase | Tipo | Por qué |
|---|---|---|
| «Malasaña representa el 85 % de esa caída» | 1 | Los hechos dicen 93 %. |
| «debido a una proporción de devoluciones más alta (7,14 %)» | 4 | Causa no demostrada. Los reembolsos fueron iguales en euros (2.000 €); lo que cae son las ventas antes de reembolsos (42.000 → 28.000 €). |
| «especialmente en tallas 41 y 42 y colores arena y negro» | 2 | Esos datos son los SKU sin stock, no las ventas que bajaron. |
| «ha afectado directamente la oferta y la capacidad de venta» | 4 | No hay datos de demanda no atendida que lo prueben. |
| «el problema es estructural en el catálogo» | 5 | Solo fueron 12 horas de reloj y solo se observan 8 SKU; los hechos no sostienen esa conclusión. |

#### Borrador C → No

| Frase | Tipo | Por qué |
|---|---|---|
| «han caído en 20.000 euros… según los registros de exportación» | 3 | Es la cifra del correo, no de los datos. La calculada es −14.000 €. |
| «se debe a devoluciones elevadas, obras… incidencias de reposición» | 3 + 4 | Causas del correo presentadas como hechos y sin datos que las prueben. |
| «reducción del 15 % en el volumen de pedidos» | 1 | No existe en los hechos de Malasaña; los pedidos fueron 120 → 120. |
| «especialmente en productos de alta rotación… disminución en la demanda efectiva» | 1 / 4 | No hay datos de rotación de productos ni de demanda. |
| «revisar el perfil de clientes y ajustar la campaña» | 4 | No hay datos de clientes ni de campañas. |

#### Borrador D → Con cambios

| Frase | Tipo | Por qué |
|---|---|---|
| «lo que sugiere una mayor frecuencia de pedidos de menor valor» | 5 | Los pedidos no aumentaron (120 → 120); bajan las unidades por pedido (3,89 → 2,53). |

### 2.3 Borrador corregido

Elijo el **borrador A**: solo tiene un error.

**Cambio:** una sola frase. El 8 eran los SKU observados, no los afectados (4), y se quita «principalmente» porque solo se observa Street One.

## 3.
### 3.3 Batería de 6 preguntas (modelo qwen3:4b-instruct, `resultados_base.json`)

| P | Pregunta | Qué pidió el modelo | ¿Correcto? | Respuesta frente a mi código |
|---|---|---|---|---|
| 1 | Ventas netas Eixample A y B | `ventas_netas` BCN-EIX ×2 (A y B) | ✅ | 24.000 € → 25.000 €, igual que el código |
| 2 | Pedidos y unidades/pedido Goya B | `cesta` MAD-GOY (B) | ✅ | 120 pedidos, 2,56 uds/pedido, igual |
| 3 | Qué cambió en las compras de Malasaña | `cesta` MAD-MAL ×2 (A y B) | ✅ | Pedidos 120 = 120; unidades 467 → 304; uds/pedido 3,89 → 2,53; ticket 350 → 233,33 €; pedidos de 4+ uds 108 → 7. Todo igual |
| 4 | Pedidos de 4+ uds en Malasaña A y B | `cesta` MAD-MAL ×2 (A y B) | ✅ | 108 → 7, igual |
| 5 | Ventas netas Malasaña del 6 al 12 de abril | `ventas_netas` MAD-MAL 2026-04-06…2026-04-12 | ✅ | 5.302,37 €, igual |
| 6 | Visitas a Malasaña en abril | Ninguna herramienta | ✅ | Dice que no hay datos de visitantes y que no estima. No se inventa nada |

- El modelo eligió siempre la herramienta adecuada, con la tienda y las fechas correctas.
- Para comparar periodos hizo dos llamadas, una por periodo, como pide la descripción.
- No ha calculado nada por su cuenta: solo repite las cifras que devuelve mi código.
- Pregunta 6: no existe ninguna herramienta de visitas, y el modelo lo reconoce en lugar
  de inventar una cifra. Esto es lo que piden las instrucciones («si ninguna herramienta
  puede responder, dilo claramente»).

### 3.4 Experimento: `--sin-contexto` (`resultados_base_sin_contexto.json`)

En este experimento, las instrucciones del modelo **no dicen qué fechas son el periodo A y el B**.
Las herramientas y su descripción son las mismas que en la batería normal.

| P | Batería normal | Sin contexto | ¿Correcto? |
|---|---|---|---|
| 1 | `ventas_netas` BCN-EIX, A y B → 24.000 € y 25.000 € | Se inventa A = ene–mar 2023 y B = abr–jun 2023 → **0 € y 0 €** | ❌ |
| 2 | `cesta` MAD-GOY B → 120 pedidos, 2,56 uds/pedido | Se inventa B = abril 2023 → **0 pedidos** | ❌ |
| 3 | `cesta` MAD-MAL A y B → todo el cambio en las compras | No usa ninguna herramienta y **pide las fechas** | ⚠️ No responde, pero no inventa |
| 4 | `cesta` MAD-MAL A y B → 108 y 7 pedidos de 4+ uds | Se inventa A = año 2023 y B = año 2024 → **0 y 0** | ❌ |
| 5 | `ventas_netas` MAD-MAL 6–12 abr 2026 → 5.302,37 € | Igual: las fechas venían en la pregunta | ✅ |
| 6 | Sin herramienta: dice que no hay datos de visitas | Igual | ✅ |

**El error sin mensaje de error:**
- En P1, P2 y P4 el modelo **se inventa las fechas** (2023 y 2024) porque no sabe qué significan
  «periodo A» y «periodo B».
- Mi función `cesta()`/`ventas_netas()` solo comprueba que la fecha tenga el formato correcto,
  no que haya datos en esas fechas. Por eso devuelve **ceros sin quejarse**.
- El modelo da esos ceros como si fueran ciertos: «Goya no registró ningún pedido», «las ventas
  netas fueron de 0,00 euros».
- **No aparece ningún error en ningún sitio:** el programa termina bien y la respuesta suena
  segura, pero es falsa. Si nadie revisa las fechas de cada llamada, no se detecta.

**Además**, el modelo no se comporta igual en todas las preguntas:
- en la P3 pide las fechas, que es lo correcto;
- en la P1, la P2 y la P4 se las inventa.

**Conclusión:** el contexto (qué fechas son A y B) es tan importante como la herramienta. Y la
barrera tiene que estar **en el código**: la función debería dar un error cuando las fechas
caen fuera de los datos, en lugar de devolver ceros. Es justo lo que plantea el reto opcional.


### 3.5 El hallazgo

| Tienda | Pedidos A → B | Uds/pedido A → B | Pedidos de 4+ uds A → B | % de pedidos con 4+ uds A → B |
|---|---|---|---|---|
| Malasaña (MAD-MAL) | 120 → 120 | 3,89 → 2,53 | **108 → 7** | 90 % → 6 % |
| Goya (MAD-GOY) | 120 → 120 | 3,25 → 2,56 | 44 → 10 | 37 % → 8 % |
| Eixample (BCN-EIX) | 120 → 120 | 2,57 → 2,46 | 10 → 5 | 8 % → 4 % |

(Fuente: `herramientas.py calcular cesta`, periodos A = 2–29 mar y B = 30 mar–26 abr.
Los % los he calculado como pedidos de 4+ / 120 pedidos.)

**¿Qué tipo de compra desaparece, y dónde?**
- Desaparecen los **pedidos grandes, de 4 o más unidades**. El número de pedidos no cambia
  (120 en todas las tiendas y periodos); lo que cambia es el tamaño de cada pedido.
- **Sobre todo en Malasaña:** pasa de 108 a 7, es decir, de 9 de cada 10 pedidos a menos de 1
  de cada 10. Con eso, sus unidades por pedido bajan de 3,89 a 2,53.
- **En Goya también bajan** (de 44 a 10), aunque partía de mucho menos.
- **En Eixample** casi no había pedidos grandes y apenas cambia (de 10 a 5).
- En el periodo B, las tres tiendas quedan parecidas (entre el 4 % y el 8 % de pedidos con
  4+ unidades). Lo raro es el periodo A de Malasaña, y en menor medida el de Goya.

**¿Qué dato pediría a la empresa?**
- **Datos de clientes:** quién hacía esos pedidos grandes en el periodo A (si eran pocos
  clientes que repetían o muchos distintos) y si han dejado de comprar o compran menos unidades.
- **Las campañas aplicadas en cada periodo:** para saber si en el periodo A había alguna
  promoción que favoreciera comprar varias unidades.
- Hoy no tenemos ninguno de los dos, así que los datos no explican por qué desaparecen.

**Recomendación para dirección:**
> Las ventas netas de Malasaña bajan de 40.000 € a 26.000 € (−14.000 €, −35 %), no 20.000 € como
> indicaba el correo, con el mismo número de pedidos (120) en ambos periodos. Lo que cambia es el
> tamaño de la compra: los pedidos de 4 o más unidades pasan de 108 a 7, y las unidades por pedido
> de 3,89 a 2,53. Goya muestra el mismo patrón en menor medida (de 44 a 10 pedidos grandes) y
> Eixample apenas cambia (de 10 a 5). Con los datos actuales no podemos explicar por qué han
> desaparecido esas compras grandes, por lo que recomendamos pedir los datos de clientes y de
> campañas aplicadas en ambos periodos antes de relanzar ninguna campaña.
