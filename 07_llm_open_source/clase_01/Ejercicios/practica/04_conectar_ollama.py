"""Conexión con Ollama: el código calcula, el modelo redacta.

Tres modos con la MISMA pregunta y el MISMO system prompt. Solo cambia el
contexto que recibe el modelo (la "escalera" de la sesión 1):

  --modo sin-datos   solo la pregunta: el modelo no sabe nada de DropLab
  --modo correo      la pregunta + el correo de dirección (con sus 20.000 €)
  --modo hechos      la pregunta + el correo + las cifras calculadas por 03
                     (modo por defecto)

Con --sin-reglas el system prompt solo fija el papel y el formato: sirve para
ver qué cambia cuando nadie le pide comprobar cifras ni admitir lo que no sabe.

El modelo nunca recibe un CSV ni calcula: como mucho recibe un JSON pequeño
con cifras ya calculadas por practica/03_metricas_basicas.py.

Salida, siempre en bloques separados:
  [LO QUE RECIBE EL MODELO]  el system prompt y el mensaje, literales
  [HECHOS]     cifras calculadas (deterministas)
  [BORRADOR]   texto del modelo (sin validar)
  [REVISIÓN]   cifras del borrador que no aparecen en los hechos
  [EJECUCIÓN]  modelo, configuración y tiempos (para anotarlos)

Ejemplos:
  python practica/04_conectar_ollama.py
  python practica/04_conectar_ollama.py --modo sin-datos
  python practica/04_conectar_ollama.py --modo correo --sin-reglas
  python practica/04_conectar_ollama.py -q "¿Fue por falta de stock?" --sin-stock
  python practica/04_conectar_ollama.py --modelo llama3.2:1b --temperatura 0.8

Requisito: Ollama en marcha y el modelo descargado (ollama pull qwen3:4b-instruct).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module

metricas = import_module("03_metricas_basicas")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "qwen3:4b-instruct"
NUM_CTX = 4096          # ventana de contexto: sobra para ~1.500 tokens y ahorra memoria
TEMPERATURA = 0.2       # baja: queremos redacción estable, no creatividad
ENCARGO = metricas.DATA.parent / "encargo_direccion.txt"
PREGUNTA = "¿Cuánto han caído realmente las ventas netas de Malasaña y qué ha cambiado en las compras?"

SYSTEM_PROMPT = """Eres el analista de datos de DropLab y redactas para dirección.

Reglas estrictas:
- Usa EXCLUSIVAMENTE las cifras del bloque "hechos" si se te entrega. No
  inventes cifras ni las recalcules.
- Si no tienes un bloque de hechos, o falta el dato que se pide, dilo
  explícitamente en lugar de inventarlo.
- Una cifra que aparece en un correo o que afirma otra persona es una
  afirmación por comprobar. Compárala con los hechos: si no coincide, dilo
  y da la cifra calculada.
- Distingue el total de la empresa de los datos de cada tienda.
- No afirmes causas. La disponibilidad de stock es una pista temporal a
  investigar, no una causa confirmada.
- Responde en español, en un máximo de 6 frases.
"""

# Sin reglas: solo el papel y el formato. Sirve para ver qué hace el modelo
# cuando nadie le pide comprobar ni admitir lo que no sabe.
SYSTEM_PROMPT_MINIMO = """Eres el analista de datos de DropLab y redactas para dirección.
Responde en español, en un máximo de 6 frases.
"""


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------


def leer_encargo() -> str:
    return ENCARGO.read_text(encoding="utf-8").strip()


def hechos_tienda(r: dict) -> dict:
    """Reorganiza el resumen de una tienda por métrica (A y B juntos).

    Un modelo pequeño lee mejor {"pedidos": {"A": 120, "B": 120}} que dos
    bloques separados por periodo. Las claves usan palabras de negocio
    («compras») para que encaje con cómo se formula la pregunta.
    """
    def ab(clave):
        return {"A": r["A"][clave], "B": r["B"][clave]}
    return {
        "local_id": r["local_id"],
        "ventas_netas": {**ab("ventas_netas"), "variacion_eur": r["variacion_neta"]["absoluta_eur"],
                         "variacion_pct": r["variacion_neta"]["porcentual"]},
        "ventas_antes_reembolsos": ab("ventas_antes_reembolsos"),
        "reembolsos_reconocidos": ab("reembolsos_reconocidos"),
        "reembolsos_sobre_ventas_pct": ab("proporcion_reembolsada_pct"),
        "compras": {
            "pedidos": ab("pedidos"),
            "unidades": ab("unidades"),
            "unidades_por_pedido": ab("unidades_por_pedido"),
            "ticket_medio_eur": ab("ticket_bruto"),
        },
    }


def construir_evidencia(incluir_stock: bool = True) -> dict:
    """Empaqueta los hechos ya calculados por 03 en un diccionario compacto."""
    ventas = metricas.cargar_ventas()
    reembolsos_local = metricas.cargar_reembolsos_con_local(ventas)

    brutas = metricas.ventas_brutas_por_periodo(ventas)
    abonos = metricas.reembolsos_por_periodo(reembolsos_local)
    netas = metricas.ventas_netas(brutas, abonos)
    absoluta, porcentual = metricas.variacion(netas["A"], netas["B"])

    netas_tienda = metricas.ventas_netas(metricas.ventas_brutas_por_periodo_y_tienda(ventas),
                                         metricas.reembolsos_por_periodo_y_tienda(reembolsos_local))

    evidencia = {
        "moneda": "EUR",
        "periodo_a": "2026-03-02 a 2026-03-29",
        "periodo_b": "2026-03-30 a 2026-04-26",
        "empresa_total": {
            "ventas_antes_reembolsos": {"A": float(brutas["A"]), "B": float(brutas["B"])},
            "reembolsos_reconocidos": {"A": float(abonos["A"]), "B": float(abonos["B"])},
            "ventas_netas": {"A": float(netas["A"]), "B": float(netas["B"])},
            "variacion_neta": {"absoluta_eur": absoluta, "porcentual": round(porcentual, 3)},
        },
        "ventas_netas_por_tienda": {
            tienda: {"A": float(fila["A"]), "B": float(fila["B"]),
                     "variacion_eur": round(float(fila["B"] - fila["A"]), 2)}
            for tienda, fila in netas_tienda.iterrows()
        },
        "malasana": hechos_tienda(metricas.resumen_tienda("MAD-MAL", ventas, reembolsos_local)),
    }
    if incluir_stock:
        disponibilidad, referencias = metricas.cargar_disponibilidad()
        evidencia["disponibilidad_cero_stock"] = metricas.resumen_cero_stock(disponibilidad, referencias,
                                                                             local_id="MAD-MAL")
    evidencia["datos_no_disponibles"] = ["visitas o tráfico", "clientes", "hora de venta", "costes y margen",
                                         "campañas aplicadas", "demanda no atendida"]
    return evidencia


def construir_mensaje(pregunta: str, modo: str, evidencia: dict | None) -> str:
    partes = [f"Pregunta: {pregunta}"]
    if modo in ("correo", "hechos"):
        partes.append(f"Correo recibido:\n{leer_encargo()}")
    if modo == "hechos" and evidencia is not None:
        partes.append("Hechos calculados (JSON, no los modifiques):\n"
                      + json.dumps(evidencia, ensure_ascii=False, indent=2))
    return "\n\n".join(partes)


def construir_payload(pregunta: str, modo: str = "hechos", evidencia: dict | None = None,
                      modelo: str = MODELO, temperatura: float = TEMPERATURA, num_ctx: int = NUM_CTX,
                      seed: int | None = None, reglas: bool = True) -> dict:
    opciones = {"num_ctx": num_ctx, "temperature": temperatura, "num_predict": 600}
    if seed is not None:
        opciones["seed"] = seed
    return {
        "model": modelo,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT if reglas else SYSTEM_PROMPT_MINIMO},
            {"role": "user", "content": construir_mensaje(pregunta, modo, evidencia)},
        ],
        "options": opciones,
        "think": False,
        "stream": False,
    }


# ---------------------------------------------------------------------------
# Llamada
# ---------------------------------------------------------------------------


def llamar_ollama(payload: dict, timeout: int = 600) -> dict:   # 10 min: portátiles sin GPU
    """Devuelve el texto y las métricas de la ejecución (o un error legible)."""
    inicio = time.time()
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        return {"error": f"No se pudo conectar con Ollama en {OLLAMA_URL}. ¿Está en marcha? Prueba 'ollama list'."}
    except requests.exceptions.Timeout:
        return {"error": "Ollama tardó demasiado en responder (timeout)."}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"Ollama devolvió un error: {exc}. ¿Está descargado el modelo {payload['model']}?"}
    cuerpo = r.json()
    ns = 1e9
    eval_s = cuerpo.get("eval_duration", 0) / ns
    return {
        "texto": cuerpo["message"]["content"].strip(),
        "segundos_total": round(time.time() - inicio, 1),
        "segundos_carga": round(cuerpo.get("load_duration", 0) / ns, 1),
        "tokens_entrada": cuerpo.get("prompt_eval_count"),
        "tokens_salida": cuerpo.get("eval_count"),
        "tokens_por_segundo": round(cuerpo.get("eval_count", 0) / eval_s, 1) if eval_s else None,
    }


def preguntar_a_ollama(pregunta: str, evidencia: dict, modo: str = "hechos", **kwargs) -> str:
    """Atajo que devuelve solo el texto (lo usa 06_flujo_visual.py)."""
    res = llamar_ollama(construir_payload(pregunta, modo, evidencia, **kwargs))
    return res.get("texto") or f"[ERROR] {res['error']}"


# ---------------------------------------------------------------------------
# Revisión automática de cifras
# ---------------------------------------------------------------------------

_NUM = re.compile(r"[−-]?\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|[−-]?\d+(?:[.,]\d+)?")


def _valores(obj) -> list[float]:
    if isinstance(obj, bool):
        return []
    if isinstance(obj, (int, float)):
        return [float(obj)]
    if isinstance(obj, dict):
        return [v for x in obj.values() for v in _valores(x)]
    if isinstance(obj, list):
        return [v for x in obj for v in _valores(x)]
    return []


def _a_float(token: str, es_porcentaje: bool) -> float | None:
    t = token.replace("−", "-").replace(" ", "")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", t):          # 40.000 o 40.000,00
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t) and not es_porcentaje:  # 40,000.00
        t = t.replace(",", "")
    else:                                                         # 3,89 · 15,625 · 3.89
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def cifras_no_respaldadas(texto: str, evidencia: dict | None) -> list[str]:
    """Cifras del borrador que no están en los hechos (ni redondeadas).

    Se ignoran los enteros pequeños sin decimales (días, conteos cortos) y los
    años. Es una ayuda para revisar, no un veredicto: una cifra puede venir del
    correo y ser citada correctamente como «lo que dice el correo».
    """
    conocidos = {abs(v) for v in _valores(evidencia or {})}
    sospechosas = []
    for m in _NUM.finditer(texto):
        token = m.group(0)
        es_pct = texto[m.end():m.end() + 2].strip().startswith("%")
        valor = _a_float(token, es_pct)
        if valor is None:
            continue
        v = abs(valor)
        decimal = bool(re.search(r"[.,]\d{1,2}$", token)) and not re.fullmatch(r"[−-]?\d{1,3}(\.\d{3})+", token)
        if (v < 100 and not decimal and not es_pct) or 2020 <= v <= 2030:
            continue
        if not any(abs(v - c) <= 0.01 or round(c, 1) == round(v, 1) or round(c) == v for c in conocidos):
            sospechosas.append(token + (" %" if es_pct else ""))
    return sorted(set(sospechosas), key=sospechosas.index)


# ---------------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description="Pregunta sobre DropLab: hechos calculados + redacción de Ollama.")
    p.add_argument("--question", "-q", default=PREGUNTA, help="Pregunta a enviar.")
    p.add_argument("--modo", choices=["sin-datos", "correo", "hechos"], default="hechos",
                   help="Qué contexto recibe el modelo (por defecto: hechos).")
    p.add_argument("--sin-stock", action="store_true", help="No incluir la disponibilidad en los hechos.")
    p.add_argument("--modelo", default=MODELO)
    p.add_argument("--temperatura", type=float, default=TEMPERATURA)
    p.add_argument("--num-ctx", type=int, default=NUM_CTX)
    p.add_argument("--seed", type=int, default=None, help="Semilla para repetir exactamente una respuesta.")
    p.add_argument("--sin-reglas", action="store_true",
                   help="System prompt mínimo, sin las reglas de verificación (para comparar).")
    a = p.parse_args()

    evidencia = construir_evidencia(incluir_stock=not a.sin_stock) if a.modo == "hechos" else None
    payload = construir_payload(a.question, a.modo, evidencia, a.modelo, a.temperatura, a.num_ctx, a.seed,
                                reglas=not a.sin_reglas)

    barra = "=" * 72
    linea = "-" * 72
    sistema = payload["messages"][0]["content"].strip()
    mensaje = payload["messages"][1]["content"].strip()
    marca = "Hechos calculados (JSON, no los modifiques):"
    if marca in mensaje:   # el JSON se imprime entero en su propio bloque, justo debajo
        mensaje = mensaje.split(marca)[0] + marca + "\n{ …el JSON completo está en [HECHOS CALCULADOS], justo debajo… }"

    print(f"{barra}\n[LO QUE RECIBE EL MODELO — modo «{a.modo}»]\n{barra}")
    print("Reglas: " + ("NO" if a.sin_reglas else "sí") + " · Correo de dirección: "
          + ("sí" if a.modo != "sin-datos" else "NO") + " · Hechos calculados: "
          + (("sí" + (" (sin disponibilidad)" if a.sin_stock else "")) if evidencia else "NO"))
    print(f"\n{linea}\n1 · SYSTEM PROMPT (instrucciones fijas: quién es y qué reglas sigue)\n{linea}")
    print(sistema)
    print(f"\n{linea}\n2 · MENSAJE (la pregunta y el contexto que le damos)\n{linea}")
    print(mensaje)

    if evidencia:
        print(f"\n{barra}\n[HECHOS CALCULADOS — fuente de verdad, deterministas]\n{barra}")
        print(json.dumps(evidencia, ensure_ascii=False, indent=2))

    res = llamar_ollama(payload)
    print(f"\n{barra}\n[BORRADOR DEL MODELO — sin validar, puede contener errores]\n{barra}")
    if "error" in res:
        print(f"[ERROR] {res['error']}")
        return
    print(res["texto"])

    print(f"\n{barra}\n[REVISIÓN — cifras del borrador que NO están en los hechos]\n{barra}")
    dudosas = cifras_no_respaldadas(res["texto"], evidencia)
    if not evidencia:
        print("Sin hechos calculados: ninguna cifra del borrador está respaldada por un cálculo.")
        if dudosas:
            print("Cifras que aparecen: " + ", ".join(dudosas))
    elif dudosas:
        print("Revisar: " + ", ".join(dudosas) + "  (¿las cita como afirmación del correo o como dato?)")
    else:
        print("Todas las cifras del borrador aparecen en los hechos. Revisa igualmente a qué se refiere cada una.")

    print(f"\n{barra}\n[EJECUCIÓN — anótalo]\n{barra}")
    print(f"Modelo: {a.modelo} · temperatura {a.temperatura} · num_ctx {a.num_ctx}"
          + (f" · seed {a.seed}" if a.seed is not None else ""))
    print(f"Tiempo total {res['segundos_total']} s (carga del modelo {res['segundos_carga']} s) · "
          f"tokens de entrada {res['tokens_entrada']} · de salida {res['tokens_salida']} · "
          f"{res['tokens_por_segundo']} tokens/s")


if __name__ == "__main__":
    main()
