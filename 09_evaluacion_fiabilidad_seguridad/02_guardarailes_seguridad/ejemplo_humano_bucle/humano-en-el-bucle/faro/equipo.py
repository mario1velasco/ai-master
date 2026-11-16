"""El equipo de Faro Digital: agentes que delegan en una persona y retoman el trabajo.

    encargo ─► supervisor ─┬─► estratega ──┐
                  ▲        ├─► redactor ───┤
                  │        ├─► persona ────┤   ← pausa: interrupt() hasta que la persona responde
                  │        └─► entregar ─► FIN
                  └────────────────────────┘

- Supervisor: decide quién trabaja a continuación (un modelo de lenguaje).
- Estratega: prepara el plan de medios con herramientas (ficha del cliente, tarifas y alcance).
- Redactor: escribe los textos de la campaña con los datos que ha confirmado la persona.
- Persona: la responsable de cuenta. No es un agente: es una persona de verdad. El equipo le
  delega lo que no puede hacer solo (aprobar un presupuesto y conseguir datos del cliente),
  el grafo se pausa con su estado guardado y, cuando ella responde, el MISMO equipo continúa.

El supervisor decide, pero hay reglas en código que no se pueden saltar: no se entrega
un plan de más de LIMITE_AUTONOMIA € sin aprobación y no se redacta sin los datos del cliente.
"""
import json
import operator
import re
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from faro import agencia
from faro.utilidades import ahora, euros, extraer_json, tokens_de

MAX_PASOS = 24          # protección frente a bucles entre agentes
MAX_RECHAZOS = 2        # si la persona rechaza el plan dos veces, el encargo se cierra


# --- Estado compartido por todo el equipo (se guarda en cada paso) ---------------
def sumar_dicts(a: dict, b: dict) -> dict:
    return {k: a.get(k, 0) + b.get(k, 0) for k in a.keys() | b.keys()}


class EstadoEncargo(TypedDict, total=False):
    encargo: dict                                   # id, cliente y brief
    plan: dict                                      # plan de medios del estratega
    aprobacion: dict                                # decisión de la persona sobre el plan
    rechazos: int
    datos_cliente: dict                             # datos que ha aportado la persona
    textos: str                                     # textos del redactor
    entrega: str                                    # propuesta final
    siguiente: str
    historial: Annotated[list, operator.add]        # quién ha hecho qué y cuándo
    tokens: Annotated[dict, sumar_dicts]            # coste por agente


def apunte(quien: str, que: str) -> dict:
    return {"quien": quien, "que": que, "cuando": ahora()}


# --- Reglas en código: lo que el equipo NO puede decidir solo ----------------------
def necesita_aprobacion(estado: EstadoEncargo) -> bool:
    plan, aprobacion = estado.get("plan"), estado.get("aprobacion")
    if not plan or plan["presupuesto_total"] <= agencia.LIMITE_AUTONOMIA:
        return False
    aprobado = aprobacion and aprobacion["decision"] in ("aprobar", "modificar")
    return not (aprobado and plan["presupuesto_total"] <= aprobacion["presupuesto_aprobado"])


def hay_que_rehacer_plan(estado: EstadoEncargo) -> bool:
    """La persona ha rechazado el plan o ha aprobado menos dinero del que pide: el estratega lo rehace."""
    plan, aprobacion = estado.get("plan"), estado.get("aprobacion")
    if not plan or not aprobacion or aprobacion["version_plan"] != plan["version"]:
        return False
    return aprobacion["decision"] == "rechazar" or plan["presupuesto_total"] > aprobacion["presupuesto_aprobado"]


def datos_pendientes(estado: EstadoEncargo) -> list[str]:
    plan = estado.get("plan") or {}
    return [d for d in plan.get("datos_que_faltan", []) if d not in estado.get("datos_cliente", {})]


def siguiente_logico(estado: EstadoEncargo) -> str:
    if not estado.get("plan") or hay_que_rehacer_plan(estado):
        return "estratega"
    if necesita_aprobacion(estado) or datos_pendientes(estado):
        return "persona"
    return "redactor" if not estado.get("textos") else "entregar"


def aplicar_reglas(estado: EstadoEncargo, propuesta: str) -> tuple[str, str | None]:
    """Devuelve el siguiente paso y, si una regla ha corregido al supervisor, el motivo."""
    propuesta = {"fin": "entregar"}.get(propuesta.strip().lower(), propuesta.strip().lower())
    logico = siguiente_logico(estado)
    if estado.get("rechazos", 0) >= MAX_RECHAZOS:
        return "entregar", "la persona ha rechazado el plan dos veces: se cierra el encargo"
    if propuesta not in ("estratega", "redactor", "persona", "entregar"):
        return logico, f"«{propuesta}» no es un miembro del equipo"
    if propuesta == logico:
        return propuesta, None
    if not estado.get("plan"):
        return logico, "todavía no hay plan"
    if hay_que_rehacer_plan(estado):
        return logico, "la persona ha pedido cambios en el plan"
    if necesita_aprobacion(estado):
        return logico, f"el plan supera {euros(agencia.LIMITE_AUTONOMIA)} y tiene que aprobarlo una persona"
    if propuesta == "persona":
        return logico, "no hay nada que pedir a la persona"
    if datos_pendientes(estado) and propuesta in ("redactor", "entregar"):
        return logico, "faltan datos que solo tiene el cliente"
    if propuesta == "entregar":
        return logico, "faltan los textos de la campaña"
    if propuesta == "estratega":
        return logico, "el plan ya está hecho y nadie ha pedido cambios"
    return propuesta, None   # p. ej., volver a redactar: se permite


# --- Herramientas del estratega ---------------------------------------------------
@tool
def consultar_ficha_cliente(cliente_id: str) -> dict:
    """[Lectura] Ficha del cliente: sector, ciudad, público, campañas anteriores y datos pendientes de confirmar."""
    return agencia.ficha_cliente(cliente_id)


@tool
def consultar_tarifas() -> dict:
    """[Lectura] Canales disponibles con su modelo de coste, coste, inversión mínima y para qué público sirven."""
    return agencia.TARIFAS


@tool
def estimar_alcance(canal: str, importe: float) -> dict:
    """[Lectura] Estima impresiones, clics o envíos de invertir un importe en euros en un canal."""
    return agencia.estimar_alcance(canal, importe)


HERRAMIENTAS = [consultar_ficha_cliente, consultar_tarifas, estimar_alcance]


def bucle_con_herramientas(modelo, mensajes: list, herramientas: list, max_iteraciones: int = 8) -> list:
    """El bucle de agente de la sesión 1: el modelo pide herramientas hasta que responde."""
    por_nombre = {h.name: h for h in herramientas}
    modelo_con_herramientas = modelo.bind_tools(herramientas)
    for _ in range(max_iteraciones):
        respuesta = modelo_con_herramientas.invoke(mensajes)
        mensajes.append(respuesta)
        if not respuesta.tool_calls:
            break
        for llamada in respuesta.tool_calls:
            herramienta = por_nombre.get(llamada["name"])
            resultado = herramienta.invoke(llamada["args"]) if herramienta else {"error": "herramienta desconocida"}
            mensajes.append(ToolMessage(json.dumps(resultado, ensure_ascii=False), tool_call_id=llamada["id"]))
    return mensajes


# --- Agentes -----------------------------------------------------------------------
def resumen_para_equipo(estado: EstadoEncargo) -> str:
    plan, aprobacion = estado.get("plan"), estado.get("aprobacion")
    lineas = [f"Encargo {estado['encargo']['id']} · cliente {estado['encargo']['cliente_id']}",
              f"Brief: {estado['encargo']['brief']}"]
    if plan:
        canales = ", ".join(f"{c['canal']} {euros(c['importe'])}" for c in plan["canales"])
        lineas.append(f"Plan v{plan['version']}: {canales} · total {euros(plan['presupuesto_total'])}")
    if aprobacion:
        lineas.append(f"Decisión de {aprobacion['respondida_por']} sobre el plan v{aprobacion['version_plan']}: "
                      f"{aprobacion['decision']}, máximo {euros(aprobacion['presupuesto_aprobado'])}. "
                      f"Comentario: {aprobacion['comentario'] or '(ninguno)'}")
    if estado.get("datos_cliente"):
        lineas.append("Datos confirmados por el cliente: " + json.dumps(estado["datos_cliente"], ensure_ascii=False))
    lineas.append(f"Datos que faltan: {datos_pendientes(estado) or 'ninguno'}")
    lineas.append(f"Textos de la campaña: {'escritos' if estado.get('textos') else 'pendientes'}")
    return "\n".join(lineas)


def crear_estratega(modelo):
    instrucciones = (
        f"Eres el estratega de medios de {agencia.AGENCIA}, una agencia de marketing para pymes. Prepara el plan "
        "de medios del encargo. Usa las herramientas: consulta la ficha del cliente y las tarifas, y estima el "
        "alcance de los canales que elijas. Elige de 2 a 4 canales y reparte el presupuesto respetando el mínimo de "
        "cada canal. Si una persona ha decidido un presupuesto máximo o ha comentado algo del plan anterior, "
        "ajústate a ello. En datos_que_faltan pon lo que solo el cliente puede confirmar y el redactor necesita "
        "(precios, fechas, fotos...). Cuando termines, responde SOLO con JSON:\n"
        '{"canales": [{"canal": "...", "importe": 0, "objetivo": "..."}], "publico": "...", '
        '"mensaje_clave": "...", "datos_que_faltan": ["..."]}')

    def leer_plan(mensajes) -> dict:
        try:
            return extraer_json(mensajes[-1].content)
        except ValueError:  # si no ha terminado en JSON, se lo pedimos una vez más
            mensajes.append(HumanMessage("Responde ahora solo con el JSON del plan."))
            mensajes.append(modelo.invoke(mensajes))
            return extraer_json(mensajes[-1].content)

    def estratega(estado: EstadoEncargo):
        aprobacion = estado.get("aprobacion") or {}
        tope = aprobacion.get("presupuesto_aprobado") if aprobacion.get("decision") == "modificar" else None
        consulta = resumen_para_equipo(estado)
        if tope:
            consulta += f"\nPRESUPUESTO MÁXIMO APROBADO: {euros(tope)}. La suma de los canales NO puede superarlo."
        mensajes = bucle_con_herramientas(modelo, [SystemMessage(instrucciones), HumanMessage(consulta)], HERRAMIENTAS)
        propuesta = leer_plan(mensajes)
        # 🐞 FALLO ENCONTRADO AL PROBAR LA DEMO CON qwen2.5:7b: Laura aprobó un máximo de 1.200 € y el
        # estratega devolvió un plan de 1.600 €. La regla del supervisor lo detectó y volvió a pedir la
        # aprobación, pero eso molesta a la persona por un error del agente. Ahora el código comprueba
        # la suma y, si se pasa, le pide al estratega que corrija (hasta dos veces) antes de seguir.
        for _ in range(2):
            total = sum(float(c.get("importe", 0)) for c in propuesta.get("canales", []))
            if not tope or total <= tope:
                break
            mensajes.append(HumanMessage(f"Tu plan suma {euros(total)} y el máximo aprobado es {euros(tope)}. "
                                         "Reduce los importes para no superarlo y responde solo con el JSON del plan."))
            mensajes.append(modelo.invoke(mensajes))
            propuesta = leer_plan(mensajes)
        canales = [{"canal": c["canal"], "importe": float(c["importe"]), "objetivo": c.get("objetivo", "")}
                   for c in propuesta.get("canales", []) if c.get("canal") in agencia.TARIFAS]
        cliente = agencia.CLIENTES.get(estado["encargo"]["cliente_id"], {})
        # Lo que la ficha marca como pendiente se pregunta siempre, lo haya detectado el modelo o no
        faltan = list(dict.fromkeys(cliente.get("pendiente_de_confirmar", []) + propuesta.get("datos_que_faltan", [])))
        plan = {"version": (estado.get("plan") or {}).get("version", 0) + 1, "canales": canales,
                # el total se calcula en código: no nos fiamos de la suma del modelo
                "presupuesto_total": round(sum(c["importe"] for c in canales), 2),
                "publico": propuesta.get("publico", ""), "mensaje_clave": propuesta.get("mensaje_clave", ""),
                "datos_que_faltan": faltan[:5]}
        resumen = ", ".join(f"{c['canal']} {euros(c['importe'])}" for c in canales)
        return {"plan": plan, "tokens": {"estratega": tokens_de(*mensajes)},
                "historial": [apunte("estratega", f"Plan v{plan['version']}: {resumen} · total "
                                                  f"{euros(plan['presupuesto_total'])}")]}
    return estratega


HUECO = re.compile(r"\s*(?:en |a |de )?\[[^\]]+\](?!\()")   # «Visítanos en [enlace a la web]»


def crear_redactor(modelo):
    instrucciones = (
        f"Eres el redactor de {agencia.AGENCIA}. Escribe los textos de la campaña: uno por canal del plan, con un "
        "titular y un texto breve adaptado al canal. Usa SOLO los datos confirmados por el cliente y su contacto "
        "(web, Instagram, teléfono) para precios, fechas y enlaces: no inventes ninguno, no dejes huecos entre "
        "corchetes y, si un dato está «(sin confirmar)», no lo menciones. Español, tono cercano. Formato: un "
        "apartado por canal.")

    def redactor(estado: EstadoEncargo):
        plan = estado["plan"]
        contacto = agencia.CLIENTES[estado["encargo"]["cliente_id"]].get("contacto", {})
        contexto = (f"{resumen_para_equipo(estado)}\nPúblico: {plan['publico']}\n"
                    f"Mensaje clave: {plan['mensaje_clave']}\nContacto del cliente: {json.dumps(contacto, ensure_ascii=False)}")
        mensajes = [SystemMessage(instrucciones), HumanMessage(contexto)]
        respuesta = modelo.invoke(mensajes)
        textos, que = respuesta.content, f"Textos escritos para {len(plan['canales'])} canales"
        # 🐞 FALLO ENCONTRADO AL PROBAR LA DEMO CON qwen2.5:7b: con datos sin confirmar, el redactor dejaba
        # huecos de relleno en los anuncios: «[Enlace a la página de reservas] (sin confirmar)» o «Visítanos en
        # [enlace a la página de Instagram]». Pedírselo otra vez no bastó: devolvió el mismo texto. Ahora:
        # 1) recibe el contacto real del cliente, 2) si aun así deja huecos se le pide que los quite, y
        # 3) si insiste, el código los elimina. Lo que llega al cliente no depende de que el modelo obedezca.
        if "sin confirmar" in textos.lower() or HUECO.search(textos):
            mensajes += [respuesta, HumanMessage("Has dejado datos sin confirmar o huecos entre corchetes (como "
                                                 "[enlace]). Quítalos del todo y devuelve los textos completos sin ellos.")]
            respuesta = modelo.invoke(mensajes)
            textos = respuesta.content
            if HUECO.search(textos):
                textos = HUECO.sub("", textos)
                que += " (el código ha quitado huecos de relleno que el modelo no quitó)"
        return {"textos": textos, "tokens": {"redactor": tokens_de(*mensajes, respuesta)},
                "historial": [apunte("redactor", que)]}
    return redactor


def crear_supervisor(modelo):
    persona = agencia.PERSONAS[agencia.PERSONA_POR_DEFECTO]
    instrucciones = (
        f"Eres el supervisor del equipo de {agencia.AGENCIA}. Tu equipo:\n"
        "- estratega: prepara o rehace el plan de medios y el presupuesto.\n"
        "- redactor: escribe los textos de la campaña cuando el plan está listo.\n"
        f"- persona: {persona['nombre']}, {persona['rol']}. Es una persona, no un agente: aprueba planes de más "
        f"de {euros(agencia.LIMITE_AUTONOMIA)} y consigue del cliente los datos que faltan. Tarda horas en "
        "responder, así que delégale solo lo necesario.\n"
        "- entregar: cierra el encargo cuando hay plan, aprobación si hace falta y textos.\n"
        'Decide quién trabaja ahora. Responde solo con JSON: {"siguiente": "...", "motivo": "..."}')

    def supervisor(estado: EstadoEncargo):
        tokens = 0
        if estado.get("textos") and not necesita_aprobacion(estado) and not hay_que_rehacer_plan(estado):
            propuesta, motivo = "entregar", "plan y textos listos"   # no hace falta preguntar al modelo
        else:
            respuesta = modelo.invoke([SystemMessage(instrucciones), HumanMessage(resumen_para_equipo(estado))])
            tokens = tokens_de(respuesta)
            try:
                decision = extraer_json(respuesta.content)
            except ValueError:
                decision = {"siguiente": "", "motivo": "respuesta no válida del modelo"}
            propuesta, motivo = decision.get("siguiente", ""), decision.get("motivo", "")
        if len(estado.get("historial", [])) >= MAX_PASOS:
            propuesta, motivo = "entregar", "demasiados pasos"
        siguiente, regla = aplicar_reglas(estado, propuesta)
        que = f"→ {siguiente}: {motivo}" if not regla else f"→ {siguiente} (proponía {propuesta or '?'}; regla: {regla})"
        return {"siguiente": siguiente, "tokens": {"supervisor": tokens}, "historial": [apunte("supervisor", que)]}
    return supervisor


# --- La persona: aquí el grafo se pausa ------------------------------------------
def preparar_tarea(estado: EstadoEncargo) -> dict:
    """Lo que verá la persona en su bandeja. Se calcula a partir del estado, sin efectos."""
    plan, encargo = estado["plan"], estado["encargo"]
    base = {"encargo_id": encargo["id"], "cliente": agencia.CLIENTES[encargo["cliente_id"]]["nombre"],
            "brief": encargo["brief"], "plan": plan}
    if necesita_aprobacion(estado):
        return base | {"tipo": "aprobacion", "titulo": f"Aprobar el plan v{plan['version']} "
                                                       f"({euros(plan['presupuesto_total'])})",
                       "instrucciones": (f"El plan supera los {euros(agencia.LIMITE_AUTONOMIA)} que el equipo puede "
                                         "decidir solo. Apruébalo, apruébalo con otro presupuesto máximo o "
                                         "recházalo con un comentario para el estratega.")}
    return base | {"tipo": "datos", "titulo": "Confirmar con el cliente los datos que faltan",
                   "instrucciones": ("El redactor necesita estos datos para escribir los textos y no los puede "
                                     "averiguar. Confírmalos con el cliente (por teléfono o email) y escríbelos aquí."),
                   "preguntas": datos_pendientes(estado)}


def persona(estado: EstadoEncargo):
    tarea = preparar_tarea(estado)
    # ⏸️ interrupt() detiene el grafo y guarda el estado en la base de datos. El proceso puede
    # terminar: cuando la persona responda, se reanuda con Command(resume=respuesta) y esta
    # función se ejecuta OTRA VEZ desde el principio, y interrupt() devuelve la respuesta.
    # Por eso antes de interrupt() no debe haber efectos (enviar un email, cobrar...): se repetirían.
    respuesta = interrupt(tarea)
    quien = respuesta.get("respondida_por", "La persona")
    if tarea["tipo"] == "aprobacion":
        decision = respuesta.get("decision", "rechazar")
        maximo = float(respuesta.get("presupuesto") or 0) if decision == "modificar" else (
            tarea["plan"]["presupuesto_total"] if decision == "aprobar" else 0)
        aprobacion = {"decision": decision, "presupuesto_aprobado": maximo, "version_plan": tarea["plan"]["version"],
                      "comentario": respuesta.get("comentario", ""), "respondida_por": quien}
        texto = {"aprobar": "aprueba el plan", "modificar": f"aprueba un máximo de {euros(maximo)}",
                 "rechazar": "rechaza el plan"}[decision]
        return {"aprobacion": aprobacion, "rechazos": estado.get("rechazos", 0) + (decision == "rechazar"),
                "historial": [apunte(quien, f"{texto}. {aprobacion['comentario']}".strip())]}
    datos = {p: v.strip() for p, v in respuesta.get("respuestas", {}).items() if v and v.strip()}
    aportados = len(datos)
    # si deja alguna pregunta sin responder, se marca para que el equipo no vuelva a preguntar
    datos |= {p: "(sin confirmar)" for p in tarea["preguntas"] if p not in datos}
    return {"datos_cliente": estado.get("datos_cliente", {}) | datos,
            "historial": [apunte(quien, f"aporta {aportados} de {len(tarea['preguntas'])} datos del cliente")]}


# --- Cierre ------------------------------------------------------------------------
def entregar(estado: EstadoEncargo):
    plan, encargo, aprobacion = estado.get("plan") or {}, estado["encargo"], estado.get("aprobacion")
    cliente = agencia.CLIENTES[encargo["cliente_id"]]["nombre"]
    if estado.get("rechazos", 0) >= MAX_RECHAZOS:
        texto = f"# Encargo {encargo['id']} · {cliente}\n\nCerrado sin campaña: el plan se rechazó dos veces.\n"
        return {"entrega": texto, "historial": [apunte("entregar", "Encargo cerrado sin campaña")]}
    filas = "\n".join(f"| {c['canal']} | {euros(c['importe'])} | {c['objetivo']} |" for c in plan["canales"])
    datos = "\n".join(f"- {p}: {v}" for p, v in estado.get("datos_cliente", {}).items()) or "- (ninguno)"
    if aprobacion:
        decision = (f"{aprobacion['decision']} por {aprobacion['respondida_por']}, máximo "
                    f"{euros(aprobacion['presupuesto_aprobado'])}")
    else:
        decision = f"no hacía falta (menos de {euros(agencia.LIMITE_AUTONOMIA)})"
    texto = (f"# Propuesta de campaña · {cliente}\n\nEncargo {encargo['id']}\n\n## Plan de medios (v{plan['version']})\n\n"
             f"| Canal | Importe | Objetivo |\n|---|---|---|\n{filas}\n\n**Total: {euros(plan['presupuesto_total'])}**"
             f" · Aprobación: {decision}\n\nPúblico: {plan['publico']}\n\nMensaje clave: {plan['mensaje_clave']}\n\n"
             f"## Datos confirmados con el cliente\n\n{datos}\n\n## Textos\n\n{estado.get('textos', '')}\n")
    return {"entrega": texto, "historial": [apunte("entregar", "Propuesta terminada")]}


# --- Montaje del grafo -------------------------------------------------------------
def construir_equipo(modelo, checkpointer):
    grafo = StateGraph(EstadoEncargo)
    grafo.add_node("supervisor", crear_supervisor(modelo))
    grafo.add_node("estratega", crear_estratega(modelo))
    grafo.add_node("redactor", crear_redactor(modelo))
    grafo.add_node("persona", persona)
    grafo.add_node("entregar", entregar)
    grafo.add_edge(START, "supervisor")
    for nodo in ("estratega", "redactor", "persona"):
        grafo.add_edge(nodo, "supervisor")      # todos vuelven al supervisor: también la persona
    grafo.add_conditional_edges("supervisor", lambda e: e["siguiente"], ["estratega", "redactor", "persona", "entregar"])
    grafo.add_edge("entregar", END)
    # Sin checkpointer, interrupt() no funciona: no habría dónde guardar el estado mientras se espera
    return grafo.compile(checkpointer=checkpointer)
