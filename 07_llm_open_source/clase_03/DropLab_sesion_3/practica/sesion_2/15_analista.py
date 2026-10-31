"""El analista completo: cifras de los datos y fuentes de los documentos, en una respuesta.

Junta lo de toda la sesión. El modelo tiene DOS herramientas y decide cuál usar:
  consultar_datos(consulta)    SQL sobre la capa semántica (bloque I): cifras exactas
  buscar_documentos(pregunta)  el RAG (bloque III): fragmentos con fuente, fecha y estado
                               (incluida la llamada transcrita con Whisper, bloque II)

Reglas: cada cifra sale de una consulta [S#]; cada hecho documental, de un fragmento [D#].
El código numera las consultas y los fragmentos, construye la lista de fuentes y verifica
que cada número de la respuesta aparece en algún resultado.

Uso:
  python practica/sesion_2/15_analista.py
  python practica/sesion_2/15_analista.py -q "¿La rotura de stock del 6 de abril explica la caída de Malasaña?"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "sesion_1"))
capa = import_module("02_capa_semantica")
asistente = import_module("01_preguntar_datos")
buscar = import_module("12_buscar")
rag = import_module("13_preguntar_documentos")

OLLAMA = "http://localhost:11434/api/chat"
LLM = "qwen3:30b-a3b-instruct-2507-q4_K_M"
PREGUNTA = ("¿Qué cambió en Malasaña a partir del 30 de marzo? Da las cifras clave y la explicación que respaldan "
            "los documentos, y di qué falta para confirmarla.")

TOOLS = [
    {"type": "function", "function": {
        "name": "consultar_datos",
        "description": "Ejecuta UNA consulta SELECT (DuckDB) sobre las vistas de ventas de DropLab y devuelve el resultado. "
                       "Para cualquier cifra: ventas, abonos, netas, pedidos, unidades, stock.",
        "parameters": {"type": "object", "properties": {"consulta": {"type": "string"}}, "required": ["consulta"]}}},
    {"type": "function", "function": {
        "name": "buscar_documentos",
        "description": "Busca en los documentos internos de DropLab (campañas, diario de tienda, logística, obras, manual, "
                       "expediente) y en la llamada del 07/04. Devuelve fragmentos con su fuente, fecha y estado.",
        "parameters": {"type": "object", "properties": {"pregunta": {"type": "string"}}, "required": ["pregunta"]}}},
]

REGLAS = """Eres el analista de DropLab y preparas una respuesta para dirección.
Tienes dos herramientas: consultar_datos (cifras exactas con SQL) y buscar_documentos (hechos con fuente).
- Toda cifra sale de consultar_datos y se cita con su número [S1], [S2]…
- Todo hecho documental sale de buscar_documentos y se cita con su fragmento [D1], [D2]…
- Separa: cifras (qué pasó), hechos documentados (qué se sabe), hipótesis (qué lo explicaría) y qué falta.
- Coincidir en el tiempo no prueba una causa. Un borrador sustituido no describe lo aplicado.
- Antes de responder, usa las DOS herramientas: no respondas nunca de memoria.
- Responde en español, en un máximo de 8 frases.

""" + capa.GUIA + "\n\n" + capa.PERIODOS


def main() -> None:
    ap = argparse.ArgumentParser(description="Analista: datos (SQL) + documentos (RAG), con fuentes.")
    ap.add_argument("--question", "-q", default=PREGUNTA)
    ap.add_argument("--llm", default=LLM)
    ap.add_argument("--guardar", type=Path, help="Guardar respuesta, llamadas y fuentes en JSON.")
    a = ap.parse_args()
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    c = Console()

    con = capa.abrir()
    sistema = REGLAS + "\n\nEsquema de las vistas:\n" + capa.esquema(con)
    b = buscar.Buscador()
    consultas, fragmentos, fuentes_texto = [], [], [a.question, capa.PERIODOS]

    def consultar_datos(consulta: str = "", **_) -> str:
        ok, res = capa.ejecutar_sql(con, consulta)
        n = len(consultas) + 1
        consultas.append({"n": n, "sql": consulta, "ok": ok, "resultado": res})
        fuentes_texto.append(res)
        return f"[S{n}] " + res

    def buscar_documentos(pregunta: str = "", **_) -> str:
        salida = []
        for f in b.buscar(pregunta, "hibrida", 4):
            if any(f["id"] == x["id"] for x in fragmentos):
                n = next(i for i, x in enumerate(fragmentos, 1) if x["id"] == f["id"])
            else:
                fragmentos.append(f)
                n = len(fragmentos)
                fuentes_texto.append(f["texto"])
            extra = f" · SUSTITUIDO por {f['sustituido_por']}" if f.get("sustituido_por") else ""
            salida.append(f"[D{n}] {f['cita']} · estado: {f['estado']}{extra} · fecha: {f['fecha']}\n{f['texto']}")
        return "\n\n".join(salida)

    herramientas = {"consultar_datos": consultar_datos, "buscar_documentos": buscar_documentos}
    messages = [{"role": "system", "content": sistema}, {"role": "user", "content": a.question}]
    c.rule(f"[bold cyan]«{a.question}»")
    t0 = time.time()
    respuesta, registro = "", []
    for ronda in range(8):
        payload = {"model": a.llm, "messages": messages, "stream": False, "think": False,
                   "options": {"num_ctx": 16384, "temperature": 0, "num_predict": 900}}
        if ronda < 7:
            payload["tools"] = TOOLS
        m = requests.post(OLLAMA, json=payload, timeout=900).json()["message"]
        llamadas = m.get("tool_calls") or []
        if not llamadas and (not consultas or not fragmentos) and ronda < 6:
            # Respondió sin consultar: el código no lo acepta y se lo devuelve (sin herramientas, inventa).
            falta = "consultar_datos" if not consultas else "buscar_documentos"
            c.print(f"[yellow]↩ Respondió sin usar {falta}: el código le pide que la use antes de responder.[/]")
            messages.append({"role": "assistant", "content": m.get("content", "")})
            messages.append({"role": "user", "content": f"No respondas todavía: usa antes la herramienta {falta}. "
                             "Toda cifra debe salir de consultar_datos y todo hecho de buscar_documentos."})
            continue
        if not llamadas:
            respuesta = (m.get("content") or "").strip()
            break
        messages.append({"role": "assistant", "content": m.get("content", ""), "tool_calls": llamadas})
        for ll in llamadas:
            nombre, args = ll["function"]["name"], ll["function"].get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args or "{}")
            res = herramientas.get(nombre, lambda **_: "Herramienta desconocida")(**args)
            icono = "🔢" if nombre == "consultar_datos" else "📄"
            detalle = args.get("consulta") or args.get("pregunta") or ""
            c.print(f"{icono} [bold]{nombre}[/] [dim]{' '.join(detalle.split())[:140]}[/]")
            registro.append((nombre, " ".join(detalle.split())))
            messages.append({"role": "tool", "content": res, "tool_name": nombre})

    c.print(Panel(respuesta, title=f"Respuesta ({a.llm}) · {time.time() - t0:.0f} s", border_style="green"))
    t = Table(title="Fuentes (las numera el código)")
    for col in ("Cita", "Qué es", "Detalle"):
        t.add_column(col)
    citadas = set(re.findall(r"\[([SD]\d+)\]", respuesta))
    for q in consultas:
        if f"S{q['n']}" in citadas:
            t.add_row(f"[S{q['n']}]", "consulta SQL", " ".join(q["sql"].split())[:90] + f" → {q['resultado'][:60]}")
    for n, f in enumerate(fragmentos, 1):
        if f"D{n}" in citadas:
            t.add_row(f"[D{n}]", f["estado"], f"{f['cita']} · {f['fecha']}")
    c.print(t)
    sin_respaldo = asistente.cifras_sin_respaldo(re.sub(r"\[[SD]\d+\]", " ", respuesta), fuentes_texto)
    sin_respaldo = [x for x in sin_respaldo if x not in (2026,)]
    if sin_respaldo:
        c.print(f"[yellow]⚠ Cifras que no aparecen en ninguna consulta ni fragmento: {', '.join(f'{x:g}' for x in sin_respaldo)}[/]")
    else:
        c.print("[green]✓ Cada cifra de la respuesta aparece en una consulta o en un fragmento.[/]")
    if a.guardar:
        a.guardar.write_text(json.dumps({
            "pregunta": a.question, "respuesta": respuesta, "respuesta_corta": respuesta, "llamadas": registro,
            "consultas": consultas, "fragmentos_citados": [f["cita"] for n, f in enumerate(fragmentos, 1) if f"D{n}" in citadas],
            "sin_respaldo": sin_respaldo, "segundos": round(time.time() - t0, 1)}, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")


if __name__ == "__main__":
    main()
