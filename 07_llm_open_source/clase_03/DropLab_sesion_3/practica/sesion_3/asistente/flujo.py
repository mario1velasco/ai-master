"""El flujo del Asistente DropLab, con LangGraph.

    planificar ──► (enrutar) ──► leer_imagen ─┐
                     ▲   │                    │
                     │   ├──► consultar_datos ─┤   cada nodo vuelve a «enrutar», que elige
                     │   └──► buscar_documentos┤   la siguiente tarea pendiente
                     └────────────────────────┘
                     │
                     └──► contrastar ──► redactar ──► verificar ──► FIN
                                            ▲              │
                                            └── 1 reintento si la verificación falla

Vocabulario:
    estado        lo que el proceso conserva y se va pasando de un nodo a otro (Estado, abajo)
    nodo          una función que recibe el estado y devuelve lo que cambia
    enrutamiento  la función que decide el siguiente nodo (enrutar, tras_verificar)

Quién decide qué:
    - el MODELO propone el plan (qué tareas hacen falta) con un esquema JSON; el CÓDIGO lo valida con
      Pydantic, lo corrige (si hay imagen, se lee) y, si falla, usa reglas;
    - las cifras, la lectura de la imagen frente a caja y los contrastes entre fuentes los hace el CÓDIGO;
    - el modelo REDACTA con las evidencias numeradas [S#] [D#] [V#], y el código verifica la redacción.

La traza es lo que se puede observar (pasos, herramientas, fuentes y tiempos), no el «razonamiento» del modelo.
"""

from __future__ import annotations

import json
import operator
import re
import time
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, ValidationError

from . import config, datos, documentos, vision
from .ollama import ErrorComponente, chat
from .sesion2 import preguntar_datos

TAREAS = ("imagen", "cifras", "documentos")


class Plan(BaseModel):
    """Lo que el modelo puede proponer. Cualquier otra cosa no pasa la validación."""
    tareas: list[Literal["imagen", "cifras", "documentos"]] = Field(description="Qué hace falta para responder")
    tienda: Literal["MAD-MAL", "MAD-GOY", "BCN-EIX"] | None = Field(None, description="Tienda de la que se pregunta")
    consulta: Literal["resumen_tienda", "pedido", "sql_libre", "ninguna"] = Field(
        "ninguna", description="resumen_tienda = cifras clave por periodo; pedido = un pedido concreto; "
                               "sql_libre = otra cifra que no cabe en las anteriores")
    motivo: str = Field("", description="Una frase corta (15 palabras como mucho): por qué")


class Estado(TypedDict, total=False):
    pregunta: str
    imagen: bytes | None
    tipo_imagen: str | None
    ajustes: dict                      # modelos y planificador
    plan: dict
    hechas: list[str]
    vision: dict | None
    consultas: list[dict]              # → [S#]
    fragmentos: list[dict]             # → [D#]
    comprobaciones: list[dict]         # contrastes hechos por el código
    limitaciones: list[str]
    respuesta: str
    avisos_verificacion: list[str]
    intentos: int
    traza: Annotated[list[dict], operator.add]
    errores: Annotated[list[dict], operator.add]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _paso(nodo: str, t0: float, herramienta: str = "", detalle: str = "", **extra) -> dict:
    return {"nodo": nodo, "segundos": round(time.time() - t0, 1), "herramienta": herramienta, "detalle": detalle, **extra}


PEDIDO_EN_TEXTO = re.compile(r"\b(?:[AB]-(?:MAD-MAL|MAD-GOY|BCN-EIX)-ORD-\d{4}|HIST-ORDER-\d{3})\b", re.I)
TIENDA_EN_TEXTO = {"MAD-MAL": r"malasa[ñn]a|mad-mal", "MAD-GOY": r"goya|mad-goy", "BCN-EIX": r"eixample|bcn-eix"}
# Junio (segundo encargo): solo hay DOCUMENTOS (los PDF leídos por PaddleOCR-VL). Los CSV acaban el 26/04.
JUNIO = re.compile(r"\bjunio\b|/06/2026|LOG-2026-06|REC-2026-0617|A-0617-04|INC-0617|RC-0620|reposici[óo]n de (?:junio|verano)|"
                   r"\bG1\b|\bT1\b|\bT2\b|cuarentena|l[íi]neas completas", re.I)
PISTA_IMAGEN = {"ticket": r"ticket|justificante|recibo|compra", "recuento": r"recuento|hoja de stock|conteo",
                "albaran": r"albar[áa]n|reparto|entrega"}


def tienda_en(texto: str) -> str | None:
    t = texto.lower()
    return next((k for k, p in TIENDA_EN_TEXTO.items() if re.search(p, t)), None)


def plan_por_reglas(pregunta: str, hay_imagen: bool) -> Plan:
    """El plan B: palabras clave. Predecible, pero rígido."""
    q = pregunta.lower()
    tareas = []
    if hay_imagen:
        tareas.append("imagen")
    cifras = re.search(r"venta|neto|neta|cifra|cu[áa]nt|pedido|unidad|abono|reembols|€|euro|ca[íi]d|baj|sub|stock|"
                       r"disponib|cesta|ticket medio|caja", q)
    docs = re.search(r"por qu[ée]|document|campa[ñn]a|pack|obra|llamada|regla|pol[íi]tica|borrador|vigen|aviso|"
                     r"log[íi]stic|albar[áa]n|explica|qu[ée] dice|aporta|causa|reposici|manual|diario|deber[íi]a", q)
    if cifras:
        tareas.append("cifras")
    if docs or not tareas:
        tareas.append("documentos")
    pedido = PEDIDO_EN_TEXTO.search(pregunta)
    consulta = "pedido" if pedido else ("resumen_tienda" if cifras else "ninguna")
    return Plan(tareas=tareas, tienda=tienda_en(pregunta), consulta=consulta, motivo="reglas de palabras clave")


# ---------------------------------------------------------------------------
# Nodos
# ---------------------------------------------------------------------------

def planificar(e: Estado) -> dict:
    t0 = time.time()
    hay_imagen = bool(e.get("imagen"))
    modo = e["ajustes"].get("planificador", "modelo")
    plan, origen, nota = None, "reglas", ""
    if modo == "modelo":
        try:
            r = chat(e["ajustes"]["modelo_texto"], [
                {"role": "system", "content": "Decides qué fuentes hacen falta para responder una pregunta sobre DropLab "
                 "(tres tiendas: Malasaña MAD-MAL, Goya MAD-GOY, Eixample BCN-EIX; periodos A=marzo y B=abril de 2026).\n"
                 "- imagen: el usuario ha adjuntado una imagen (ticket, recuento o albarán) que hay que leer y comprobar.\n"
                 "- cifras: hace falta algún número de ventas, abonos, pedidos, unidades o stock.\n"
                 "- documentos: hacen falta hechos, fechas, reglas o explicaciones (campañas, obras, logística, la llamada).\n"
                 "Junio (reposición de Street One, informe LOG-2026-06, expediente REC-2026-0617) NO está en los datos: "
                 "los datos acaban el 26/04; de junio solo hay documentos.\n"
                 "Elige SOLO lo imprescindible: cada tarea cuesta tiempo. Ejemplos:\n"
                 "- «¿Qué demuestra este ticket?» con imagen → [imagen]\n"
                 "- «¿Cuánto cayó el neto de Goya?» → [cifras], consulta resumen_tienda, tienda MAD-GOY\n"
                 "- «¿Hasta cuándo duró el Pack 4?» → [documentos]\n"
                 "- «¿Qué cambió en Malasaña y por qué?» → [cifras, documentos]\n"
                 "- «¿Cuántos pares aceptó Malasaña en junio?» → [documentos]\n"
                 "Responde en JSON."},
                {"role": "user", "content": f"Pregunta: {e['pregunta']}\nImagen adjunta: {'sí' if hay_imagen else 'no'}"}],
                formato=Plan.model_json_schema(), num_ctx=config.CTX_TEXTO, num_predict=300)   # 150 se quedaba corto: JSON cortado → reglas
            plan = Plan.model_validate_json(r.contenido)
            origen = "modelo"
        except ValidationError as exc:
            nota = f"plan del modelo no válido ({exc.error_count()} error(es)): se usan reglas"
        except ErrorComponente as exc:
            nota = f"{exc.codigo}: se usan reglas"
    if plan is None:
        plan = plan_por_reglas(e["pregunta"], hay_imagen)
    # El código corrige el plan: la imagen se lee si existe y solo si existe; un pedido en la pregunta, se consulta
    tareas = [t for t in TAREAS if t in plan.tareas and (t != "imagen" or hay_imagen)]
    if hay_imagen and "imagen" not in tareas:
        tareas.insert(0, "imagen")
        nota = (nota + "; " if nota else "") + "había imagen y el plan no la leía: se añade"
    if PEDIDO_EN_TEXTO.search(e["pregunta"]):
        plan.consulta = "pedido"
        if "cifras" not in tareas:
            tareas.append("cifras")
    if JUNIO.search(e["pregunta"]) and not re.search(r"marzo|abril|periodo [AB]\b", e["pregunta"], re.I):
        if "cifras" in tareas:
            tareas.remove("cifras")
            nota = (nota + "; " if nota else "") + "junio no está en los datos (acaban el 26/04): solo documentos"
        if "documentos" not in tareas:
            tareas.append("documentos")
    if "cifras" in tareas and plan.consulta == "ninguna":
        plan.consulta = "resumen_tienda"
    if not tareas:
        tareas = ["documentos"]
    plan_final = {"tareas": tareas, "tienda": plan.tienda or tienda_en(e["pregunta"]), "consulta": plan.consulta,
                  "motivo": plan.motivo, "origen": origen, "nota": nota}
    return {"plan": plan_final, "hechas": [], "consultas": [], "fragmentos": [], "comprobaciones": [],
            "limitaciones": [], "intentos": 0,
            "traza": [_paso("planificar", t0, f"plan por {origen}", " → ".join(tareas) + (f" ({nota})" if nota else ""),
                            plan=plan_final)]}


def enrutar(e: Estado) -> str:
    """Enrutamiento: la siguiente tarea pendiente, en orden fijo; si no queda ninguna, contrastar."""
    nodo = {"imagen": "leer_imagen", "cifras": "consultar_datos", "documentos": "buscar_documentos"}
    for t in e["plan"]["tareas"]:
        if t not in e.get("hechas", []):
            return nodo[t]
    return "contrastar"


def leer_imagen(e: Estado) -> dict:
    t0 = time.time()
    tipo = e.get("tipo_imagen")
    if not tipo:
        tipo = next((k for k, p in PISTA_IMAGEN.items() if re.search(p, e["pregunta"].lower())), None)
    try:
        r = vision.analizar_imagen(e["imagen"], tipo=tipo, modelo=e["ajustes"]["modelo_vision"],
                                   usar_cache=e["ajustes"].get("reutilizar_lecturas", True))
    except ErrorComponente as exc:
        return {"hechas": e["hechas"] + ["imagen"], "vision": None, "errores": [exc.como_dict()],
                "traza": [_paso("leer_imagen", t0, "VLM", f"error: {exc.codigo}")]}
    ex = r["extraccion"]
    det = (f"{r['tipo']} · {ex['modelo']} · {'JSON válido' if ex['valido'] else 'JSON NO válido'}"
           + (f" · {r['comprobacion']['veredicto']}" if r["comprobacion"] else "")
           + (" · lectura REUTILIZADA (misma imagen ya leída: caché por huella sha256)" if ex["reutilizada"] else ""))
    return {"hechas": e["hechas"] + ["imagen"], "vision": r,
            "traza": [_paso("leer_imagen", t0, "VLM + Pydantic + SQL con parámetros", det, pasos=r["pasos"])]}


def consultar_datos(e: Estado) -> dict:
    t0 = time.time()
    plan = e["plan"]
    consultas, errores, herramienta = list(e.get("consultas", [])), [], plan["consulta"]
    try:
        if plan["consulta"] == "pedido":
            m = PEDIDO_EN_TEXTO.search(e["pregunta"])
            if m:
                p = datos.pedido(m[0].upper())
                consultas += [{k: p[k] for k in ("herramienta", "titulo", "sql", "parametros", "filas")},
                              {k: p["abonos"][k] for k in ("herramienta", "titulo", "sql", "parametros", "filas")}]
            else:
                herramienta = "resumen_tienda"
        if plan["consulta"] == "sql_libre":
            r = datos.preguntar(e["pregunta"], e["ajustes"]["modelo_texto"])
            for c in r["consultas"]:
                if c["ok"]:
                    consultas.append({"herramienta": "sql_del_modelo", "titulo": "SQL escrito por el modelo (con barreras)",
                                      "sql": c["sql"], "parametros": [], "filas": json.loads(c["resultado"].split("  (")[0])})
            if r.get("aviso"):
                errores.append({"codigo": "CIFRAS_SIN_RESPALDO", "componente": "datos", "mensaje": r["aviso"]})
        if herramienta == "resumen_tienda" or plan["consulta"] == "resumen_tienda":
            consultas.append(datos.resumen_tienda(plan.get("tienda") or "MAD-MAL"))
    except ErrorComponente as exc:
        errores.append(exc.como_dict())
    nuevas = consultas[len(e.get("consultas", [])):]
    return {"hechas": e["hechas"] + ["cifras"], "consultas": consultas, "errores": errores,
            "traza": [_paso("consultar_datos", t0, "DuckDB · capa semántica",
                            "; ".join(f"{c['herramienta']}({', '.join(dict.fromkeys(map(str, c['parametros'])))})"
                                      for c in nuevas)
                            or "sin consultas")]}


def buscar_documentos(e: Estado) -> dict:
    t0 = time.time()
    preguntas = [e["pregunta"]]
    v = e.get("vision") or {}
    if v.get("tipo") == "albaran":
        preguntas.append("entrega fallida del 6 de abril, avería y reposición alternativa")
    if v.get("tipo") == "ticket" and ((v.get("extraccion") or {}).get("datos") or {}).get("texto_campana"):
        preguntas.append("vigencia aprobada de la campaña Pack 4 y condiciones")
    frags, errores = [], []
    try:
        for q in preguntas:
            for f in documentos.buscar(q, k=5):
                if f["id"] not in {x["id"] for x in frags}:
                    frags.append(f)
    except ErrorComponente as exc:
        errores.append(exc.como_dict())
    frags = frags[:8]
    return {"hechas": e["hechas"] + ["documentos"], "fragmentos": frags, "errores": errores,
            "traza": [_paso("buscar_documentos", t0, "RAG · bge-m3 híbrida · índice "
                            + ("ampliado (sesión 2 + junio)" if documentos.estado()["ampliado"] else "de la sesión 2"),
                            f"{len(preguntas)} búsqueda(s) → {len(frags)} fragmentos: "
                            + ", ".join(f["cita"] for f in frags[:4]) + ("…" if len(frags) > 4 else ""))]}


FECHA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")


def contrastar(e: Estado) -> dict:
    """Comprobaciones entre fuentes, en código: versiones, fuentes automáticas, ticket frente a campaña, límites."""
    t0 = time.time()
    comp, lim = [], []
    frags = e.get("fragmentos") or []
    v = e.get("vision")
    if v and v.get("comprobacion"):
        c = v["comprobacion"]
        comp.append({"nombre": f"{c['tipo']} frente a los registros", "resultado": c["veredicto"],
                     "detalle": c["explicacion"][0], "fuentes": ["V1"]})
    elif v:
        comp.append({"nombre": "lectura de la imagen", "resultado": "no_valida",
                     "detalle": "La extracción no pasó la validación de Pydantic: no se compara.", "fuentes": ["V1"]})
    for f in frags:
        if f.get("sustituido_por"):
            comp.append({"nombre": "versiones", "resultado": "aviso",
                         "detalle": f"{f['cita']} está SUSTITUIDO por {f['sustituido_por']}: solo vale como antecedente.",
                         "fuentes": []})
    leidos = [f for f in frags if f.get("lectura")]
    if leidos:
        sin_comprobar = [("escaneado" if "escaneado" in f["fuente"] else "informe") + " " + f["cita"].split(" · ")[-1]
                         for f in leidos if "SIN COMPROBAR" in f["lectura"]]
        comp.append({"nombre": "lectura automática", "resultado": "aviso",
                     "detalle": f"{len(leidos)} página(s) leídas por PaddleOCR-VL, sin revisión humana. "
                                + ("Cifras que no se han podido comprobar con el texto del PDF (escaneado o gráfico): "
                                   + ", ".join(sin_comprobar) + "." if sin_comprobar else
                                   "Sus cifras coinciden con el texto del PDF."),
                     "fuentes": []})
    if any((f.get("estado") or "").startswith("transcripción") for f in frags):
        comp.append({"nombre": "fuente automática", "resultado": "aviso",
                     "detalle": "La llamada es una transcripción automática (Whisper): testimonio, no registro.",
                     "fuentes": []})
    # Ticket frente a la campaña aprobada (visión + documentos)
    if v and v.get("tipo") == "ticket" and (v.get("extraccion") or {}).get("datos"):
        t = v["extraccion"]["datos"]
        cal = documentos.fragmento_por_codigo("CAM-2026-03-FINAL", "Pack 4 |")
        m = re.search(r"MAD-MAL \| Pack 4 \| (\d{2}/\d{2}/\d{4}) \| (\d{2}/\d{2}/\d{4})", (cal or {}).get("texto", ""))
        if cal and m and t.get("fecha"):
            if cal["id"] not in {f["id"] for f in frags}:
                frags = frags + [cal]
            ini, fin = (f"{x[6:]}-{x[3:5]}-{x[:2]}" for x in m.groups())
            unidades = sum(l.get("cantidad") or 0 for l in t.get("lineas") or [])
            dentro = ini <= t["fecha"] <= fin
            detalle = (f"Ticket del {t['fecha']} con {unidades} unidades. Pack 4 aprobado: del {m[1]} al {m[2]}, "
                       f"4 o más unidades. ")
            detalle += ("Cumple las condiciones (elegible); el ticket no prueba que se entregara el regalo."
                        if dentro and unidades >= 4 else "No cumple las condiciones de Pack 4.")
            fechas = FECHA.findall(t.get("texto_campana") or "")
            if fechas:
                impresa = "/".join(fechas[-1])
                detalle += f" Vigencia impresa en el ticket: {impresa} ({'coincide' if impresa == m[2] else 'NO coincide'} con el calendario aprobado)."
            comp.append({"nombre": "ticket frente a Pack 4", "resultado": "elegible" if dentro and unidades >= 4 else "no_elegible",
                         "detalle": detalle, "fuentes": ["V1", f"D{[f['id'] for f in frags].index(cal['id']) + 1}"]})
    q = e["pregunta"].lower()
    if JUNIO.search(e["pregunta"]) and not re.search(r"marzo|abril", q):
        lim.append("Junio no está en los datos de ventas (acaban el 26/04): las cifras de junio salen solo de los "
                   "documentos de junio.")
    if re.search(r"por qu[ée]|causa|explica|culpa|demuestra|responsable|fraude|debido|fue por|se debi", q):
        lim.append("Coincidir en el tiempo no prueba una causa. Faltan datos para atribuirla: visitas o tráfico, "
                   "regalos entregados, campaña aplicada a cada pedido y demanda no atendida.")
    if re.search(r"cliente|visita|tr[áa]fico|regalos? entregad|tote bags? se entreg|margen|coste", q):
        lim.append("Ese dato no existe en DropLab: no hay clientes (un pedido no es una persona), visitas, regalos "
                   "entregados ni costes.")
    if v and v.get("tipo") == "ticket":
        lim.append("Una discrepancia en un ticket pide revisión; no demuestra fraude ni dice quién se equivocó.")
    if v and v.get("tipo") == "albaran":
        lim.append("Un albarán con unidades previstas no demuestra que se recibieran.")
    return {"comprobaciones": comp, "limitaciones": lim, "fragmentos": frags,
            "traza": [_paso("contrastar", t0, "código", f"{len(comp)} comprobación(es) · {len(lim)} límite(s)")]}


REGLAS_REDACCION = """Eres el analista de DropLab y respondes a dirección usando SOLO las evidencias que se te dan.
Reglas:
- Cada afirmación lleva detrás su cita: [S#] cifras de una consulta, [D#] un documento o la llamada,
  [V#] la comprobación de una imagen. Sin cita, no se afirma.
- Las comprobaciones [V#] y las «comprobaciones del código» las hizo el código: repite su veredicto, no lo cambies.
  Una discrepancia no demuestra fraude ni dice quién se equivocó.
- Un documento SUSTITUIDO solo se menciona como antecedente. Lo previsto no prueba que ocurriera.
- Si un documento tiene «lectura: … sin revisar», se leyó con OCR: si la cifra viene de un gráfico o de un escaneado, dilo.
  Coincidir en el tiempo no prueba una causa. La llamada es una transcripción automática.
- No calcules cifras nuevas: copia las de las evidencias. Si algo no consta, dilo y di qué faltaría.
- No menciones fuentes que no aportan nada a la pregunta.
- En español, con los apartados que se indican al final (títulos en negrita, en ese orden) y ningún otro.
  Máximo 220 palabras: frases cortas, sin repetir datos."""


def evidencias(e: Estado) -> list[dict]:
    """Numera las evidencias: S (datos), D (documentos), V (imagen). La numeración la pone el código."""
    out = []
    for i, c in enumerate(e.get("consultas") or [], 1):
        out.append({"id": f"S{i}", "tipo": "datos", "titulo": c["titulo"], "sql": c["sql"], "parametros": c["parametros"],
                    "filas": c["filas"], "texto": json.dumps(c["filas"], ensure_ascii=False)})
    for i, f in enumerate(e.get("fragmentos") or [], 1):
        out.append({"id": f"D{i}", "tipo": "documento", "cita": f["cita"], "titulo": f["titulo"], "estado": f["estado"],
                    "fecha": f["fecha"], "sustituido_por": f.get("sustituido_por"), "lectura": f.get("lectura"),
                    "texto": f["texto"]})
    v = e.get("vision")
    if v:
        ex, c = v["extraccion"], v.get("comprobacion")
        texto = {"tipo": v["tipo"], "extraccion": ex.get("datos"), "veredicto": c and c["veredicto"],
                 "explicacion": c and c["explicacion"],
                 "comprobaciones": c and [{k: x[k] for k in ("campo", "en_imagen", "en_registro", "resultado")}
                                          for x in c["comprobaciones"]]}
        out.append({"id": "V1", "tipo": "imagen", "titulo": f"Lectura de la imagen ({v['tipo']}) y comprobación con los registros",
                    "modelo": ex["modelo"], "valido": ex["valido"], "extraccion": ex.get("datos"),
                    "errores_validacion": ex.get("errores_validacion"), "veredicto": c and c["veredicto"],
                    "comprobaciones": c and c["comprobaciones"], "consultas": c and c["consultas"],
                    "texto": json.dumps(texto, ensure_ascii=False)})
    return out


def redactar(e: Estado) -> dict:
    t0 = time.time()
    ev = evidencias(e)
    if not ev:
        return {"respuesta": "No he podido reunir evidencias para responder: revisa los errores.",
                "traza": [_paso("redactar", t0, "—", "sin evidencias")]}
    bloques = []
    for x in ev:
        cab = f"[{x['id']}] "
        if x["tipo"] == "datos":
            cab += f"{x['titulo']}"
        elif x["tipo"] == "documento":
            cab += f"{x['cita']} · {x['titulo']} · estado: {x['estado']} · fecha: {x['fecha']}"
            if x.get("sustituido_por"):
                cab += f" · SUSTITUIDO por {x['sustituido_por']}"
            if x.get("lectura"):
                cab += f" · lectura: {x['lectura']}"
        else:
            cab += x["titulo"]
        bloques.append(cab + "\n" + x["texto"])
    avisos = [f"- {c['nombre']}: {c['detalle']}" for c in e.get("comprobaciones") or []]
    avisos += [f"- límite: {l}" for l in e.get("limitaciones") or []]
    tipos = {x["tipo"] for x in ev}
    apartados = ["**Respuesta**"] + [t for t, k in (("**Cifras**", "datos"), ("**Documentos y llamada**", "documento"),
                                                     ("**Imagen**", "imagen")) if k in tipos] + ["**Límites**"]
    mensaje = ("Evidencias:\n\n" + "\n\n".join(bloques) + "\n\nComprobaciones del código (no son fuentes, no se citan):\n"
               + ("\n".join(avisos) or "- ninguna") + f"\n\nPregunta: {e['pregunta']}\n\nApartados: "
               + ", ".join(apartados) + "\nCitas que existen (no hay otras): " + ", ".join(f"[{x['id']}]" for x in ev)
               + ". Los límites y las comprobaciones del código no llevan cita propia.")
    if e.get("avisos_verificacion"):
        mensaje += ("\n\nTu respuesta anterior no pasó la revisión automática: " + "; ".join(e["avisos_verificacion"])
                    + ". Reescríbela usando solo cifras que aparezcan en las evidencias y citando cada frase.")
    try:
        r = chat(e["ajustes"]["modelo_texto"], [{"role": "system", "content": REGLAS_REDACCION},
                                                {"role": "user", "content": mensaje}], num_ctx=config.CTX_TEXTO, num_predict=900)
    except ErrorComponente as exc:
        return {"respuesta": "", "errores": [exc.como_dict()],
                "traza": [_paso("redactar", t0, e["ajustes"]["modelo_texto"], f"error: {exc.codigo}")]}
    return {"respuesta": r.contenido.strip(), "intentos": e.get("intentos", 0) + 1,
            "traza": [_paso("redactar", t0, r.modelo, f"{r.tokens_entrada} tokens de entrada · {r.tokens_salida} de salida · "
                            f"{r.tokens_por_segundo} tok/s" + (" · reintento" if e.get("intentos") else ""),
                            tiempos=r.tiempos())]}


CULPA = re.compile(r"\bfraude|\brobo|\bestafa|\bmanipul|\bculpa del|\berror (?:del|de la) (?:emplead|cajer|dependient)", re.I)
CAUSAL = re.compile(r"\b(?:caus[óo]|provoc[óo]|se debi[óo] a|fue debido a|explica la ca[íi]da)\b", re.I)
NEGACION = re.compile(r"\bno (?:\w+ ){0,3}(?:demuestra|prueba|indica|permite|implica|acredita|atribu)|\bni\b|\bsin\b", re.I)


def frases_con(patron: re.Pattern, texto: str) -> list[str]:
    """Frases que contienen el patrón y NO lo niegan («no demuestra fraude» está bien)."""
    frases = re.split(r"(?<=[.!?])\s+", texto)
    return [f for f in frases if patron.search(f) and not NEGACION.search(f)]


def verificar(e: Estado) -> dict:
    """El código revisa la redacción: citas que existen, cifras con respaldo, versiones y lenguaje de culpa o causa."""
    t0 = time.time()
    texto = e.get("respuesta") or ""
    ev = {x["id"]: x for x in evidencias(e)}
    avisos = []
    citadas = set(re.findall(r"\[([SDV]\d+)\]", texto))
    for c in sorted(citadas - set(ev)):
        avisos.append(f"cita inexistente [{c}]")
    fuentes = [e["pregunta"], datos.capa.PERIODOS] + [x["texto"] for x in ev.values()]
    sin_respaldo = preguntar_datos.cifras_sin_respaldo(re.sub(r"\[[SDV]\d+\]", " ", texto), fuentes)
    sin_respaldo = [x for x in sin_respaldo if x not in (2026,)]
    if sin_respaldo:
        avisos.append("cifras sin respaldo en las evidencias: " + ", ".join(f"{x:g}" for x in sin_respaldo))
    sustituidas = [i for i in citadas if ev.get(i, {}).get("sustituido_por")]
    if sustituidas and not re.search(r"borrador|sustitu|propuesta|antecedente", texto, re.I):
        avisos.append("cita un documento sustituido sin decir que es un borrador")
    if frases_con(CULPA, texto):
        avisos.append("atribuye culpa o fraude: ninguna evidencia lo permite")
    causales = [f for f in frases_con(CAUSAL, texto) if not re.search(r"hip[óo]tesis|podr[íi]a|posible", f, re.I)]
    if causales:
        avisos.append("afirma una causa sin presentarla como hipótesis")
    if not citadas and texto:
        avisos.append("la respuesta no cita ninguna evidencia")
    return {"avisos_verificacion": avisos,
            "traza": [_paso("verificar", t0, "código", "✓ limpia" if not avisos else "⚠ " + "; ".join(avisos))]}


def tras_verificar(e: Estado) -> str:
    """Si la verificación falla en lo grave (cifras o citas), un único reintento; después, FIN con avisos."""
    graves = [a for a in e.get("avisos_verificacion") or [] if a.startswith(("cifras", "cita inexistente", "la respuesta no"))]
    return "redactar" if graves and e.get("intentos", 0) < 2 else END


# ---------------------------------------------------------------------------
# El grafo
# ---------------------------------------------------------------------------

def construir():
    g = StateGraph(Estado)
    for nombre, f in (("planificar", planificar), ("leer_imagen", leer_imagen), ("consultar_datos", consultar_datos),
                      ("buscar_documentos", buscar_documentos), ("contrastar", contrastar), ("redactar", redactar),
                      ("verificar", verificar)):
        g.add_node(nombre, f)
    destinos = ["leer_imagen", "consultar_datos", "buscar_documentos", "contrastar"]
    g.add_edge(START, "planificar")
    g.add_conditional_edges("planificar", enrutar, destinos)
    for n in ("leer_imagen", "consultar_datos", "buscar_documentos"):
        g.add_conditional_edges(n, enrutar, destinos)
    g.add_edge("contrastar", "redactar")
    g.add_edge("redactar", "verificar")
    g.add_conditional_edges("verificar", tras_verificar, ["redactar", END])
    return g.compile()


GRAFO = None


def grafo():
    global GRAFO
    if GRAFO is None:
        GRAFO = construir()
    return GRAFO


def estado_inicial(pregunta: str, imagen: bytes | None = None, tipo_imagen: str | None = None,
                   modelo_texto: str | None = None, modelo_vision: str | None = None,
                   planificador: str = "modelo", reutilizar_lecturas: bool = True) -> Estado:
    if not (pregunta or "").strip():
        raise ErrorComponente("PREGUNTA_VACIA", "api", "La pregunta está vacía.")
    return {"pregunta": pregunta.strip(), "imagen": imagen, "tipo_imagen": tipo_imagen,
            "ajustes": {"modelo_texto": modelo_texto or config.MODELO_TEXTO,
                        "modelo_vision": modelo_vision or config.MODELO_VISION, "planificador": planificador,
                        "reutilizar_lecturas": reutilizar_lecturas},
            "traza": [], "errores": []}


def resultado(e: Estado, segundos: float, origen: str = "en_directo") -> dict:
    """Lo que devuelve la API: respuesta, evidencias, comprobaciones, límites, traza y errores."""
    ev = evidencias(e)
    citadas = set(re.findall(r"\[([SDV]\d+)\]", e.get("respuesta") or ""))
    for x in ev:
        x["citada"] = x["id"] in citadas
    return {"respuesta": e.get("respuesta") or "", "evidencias": ev, "comprobaciones": e.get("comprobaciones") or [],
            "limitaciones": e.get("limitaciones") or [], "verificacion": e.get("avisos_verificacion") or [],
            "plan": e.get("plan"), "traza": e.get("traza") or [], "errores": e.get("errores") or [],
            "configuracion": e["ajustes"], "segundos": round(segundos, 1), "origen": origen}


def ejecutar(pregunta: str, imagen: bytes | None = None, al_avanzar=None, **ajustes) -> dict:
    """Ejecuta el grafo. al_avanzar(nodo, cambios): para enseñar el progreso (terminal, API, Open WebUI)."""
    t0 = time.time()
    e = estado_inicial(pregunta, imagen, **ajustes)
    final = dict(e)
    for paso in grafo().stream(e, stream_mode="updates"):
        for nodo, cambios in paso.items():
            cambios = cambios or {}
            for k, v in cambios.items():
                final[k] = final.get(k, []) + v if k in ("traza", "errores") else v
            if al_avanzar:
                al_avanzar(nodo, cambios)
    return resultado(final, time.time() - t0)


def mermaid() -> str:
    return grafo().get_graph().draw_mermaid()
