# CLAUDE.md — Tema 7: LLM de código abierto (modelos locales con Ollama)

Máster EBIS Business Techschool (Automatización con IA Agéntica). Todo en **español**, lenguaje sencillo.
Formato de referencia de guías y CLAUDE.md: `../05_rag_langchain/`. Repo git sin commits todavía.

## Estructura

Una carpeta por sesión: `clase_NN/` con diapositivas, deberes/test y material práctico. Cada una tiene su
guía `EXPLICACION_tema_N.md` (lee la guía antes de responder sobre esa sesión).

| Sesión | Tema | Guía |
|---|---|---|
| `clase_01` | Caso DropLab: LLM local (Ollama) que redacta sobre cifras calculadas por código; tool calling | [EXPLICACION_tema_1.md](clase_01/EXPLICACION_tema_1.md) |

Hilo del tema: caso de negocio **DropLab** (3 tiendas, correo con −20.000 € por comprobar). Regla de oro:
**el código calcula, el modelo redacta, tú verificas.**

## Sesión 1 en breve

- Datos: 6 CSV (`DropLab/datos/`); periodos **A = 2–29 mar, B = 30 mar–26 abr**. Trampas: pedido ≠ línea ≠
  unidades, JOIN que duplica, abono cuenta por `fecha_reconocimiento`, stock solo de 8 SKU, sin visitas/costes.
- Cifras: neto 96.000 → 81.000 € (−15.000); **Malasaña 40.000 → 26.000 € (−14.000, −35 %)**, no 20.000.
- Modelo de clase `qwen3:4b-instruct` (Ollama). Un LLM no calcula (17×23 → 401). Contexto = lo que más memoria gasta.
- Con hechos + reglas redacta bien; aun así puede dar cifras reales con significado falso.
- Función fija (fiable, limitada) > SQL libre (falla sin error). Barreras en el código, no en el prompt.
- Código: `clase_01/Ejercicios/{practica,ejercicio_3,DropLab}/`.

## Entorno

- Un único `.venv` en la raíz (Python 3.11), compartido por todas las clases; nada se instala en el sistema.
  `requirements.txt` raíz incluye con `-r` el de cada clase (añadir una línea por clase nueva).
- Cómo ejecutar cada script con sus opciones: sección 12 de [EXPLICACION_tema_1.md](clase_01/EXPLICACION_tema_1.md).

## Reglas para Claude

1. Cifras contrastadas con scripts/diapositivas, no de memoria; los PDF con gráficos, verlos renderizados.
2. No ejecutar modelos de Ollama ni `ollama pull` sin petición expresa (RAM/GPU, GB).
3. **Los deberes son del usuario**: explicar y guiar, no entregarlos resueltos salvo petición clara.
4. No modificar datos ni scripts del profesor (`practica/`, `DropLab/`); `herramientas.py` sí se completa.
5. Sin `.venv`/claves en entregas. Sin commits/push salvo petición.
6. No inventar scripts citados pero ausentes (`05`, `06`, `09` de la sesión 1).
7. Nuevas sesiones: crear `EXPLICACION_tema_N.md` con el formato de las guías y añadir una fila a la tabla y,
   si aporta, un bloque "en breve" de pocas líneas.
