# Cómo se decide el orden

`scripts/_ordering.py` aplica **orden natural**: separa cada nombre en texto y números y compara los números como enteros (`parte_2` < `parte_10`). Las extensiones se ignoran.

## Cuándo el orden es claro (exit 0)

Todos los nombres tienen la misma estructura, el texto no cambia y **un único número** varía: `6_chunk_001 … 6_chunk_019`, `rec_1 … rec_12`, `reunion-01 … reunion-05`.

## Cuándo es ambiguo (exit 3 → preguntar)

| Situación | Ejemplo | Por qué se pregunta |
|---|---|---|
| Sin números | `intro.aac`, `final.aac` | Alfabético ≠ cronológico. |
| Texto del nombre distinto | `lunes_1`, `martes_1` | Pueden ser series distintas. |
| Varios números varían | `6_chunk_001`, `7_chunk_001` | No se sabe cuál manda. |
| Estructuras distintas | `a_1`, `a_1_2` | Posibles series mezcladas. |
| Números repetidos | `p_1`, `p_01` | No hay orden único. |

## Avisos (no bloquean)

Huecos en la numeración (`rec_1, rec_2, rec_5`): puede faltar un audio. Díselo al usuario.

## Cómo fijar un orden manual

Crea un fichero con un nombre por línea, en el orden confirmado por el usuario, y pásalo con `--files-from orden.txt`. También existe `--accept-order` para aceptar el orden propuesto aunque sea ambiguo, **solo** si el usuario lo ha confirmado.

## Fechas de modificación

No se usan para ordenar: copiar o descargar archivos las altera.
