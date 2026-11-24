"""El grafo del agente de Ondo.

    interpretar ─┬─ seguridad / persona ─────────────────────► escalar ──┐
                 ├─ no entendido ──► reparar ──(3.º intento)──► escalar ──┤
                 ├─ información / saludo ──► informar / saludar ──────────┤
                 └─ pedido / devolución / cita                            │
                        └─► identificar ──► flujo_* ──(persona)──► escalar┤
                                                                          ▼
                                                                      redactar ──► FIN

Los nodos deciden QUÉ hay que decir (dejan un "borrador"); el nodo redactar
decide CÓMO decirlo (tono, idioma, formato del canal).
"""

import re

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from . import llm
from .estado import Estado
from .flujos.cita import flujo_cita
from .flujos.comun import MENU, borrador, fin_de_flujo
from .flujos.devolucion import flujo_devolucion
from .flujos.pedido import flujo_pedido

MAX_INTENTOS = (
    3  # al tercer mensaje seguido sin entender al cliente, pasa a una persona
)
FLUJOS = {
    "pedido": "flujo_pedido",
    "devolucion": "flujo_devolucion",
    "cita": "flujo_cita",
}
MENU_INTENCION = dict(zip(MENU, ["pedido", "devolucion", "cita", "persona"]))

# Red de seguridad que no depende del modelo: estas palabras siempre son un caso de seguridad.
PELIGRO = re.compile(
    r"quemad|humo|fuego|se calienta|muy caliente|hinchad|chispa|los frenos no|no frena|sin frenos|"
    r"burning|smoke|brûl|fumée|bruciat|fumo|queimad|fumo",
    re.IGNORECASE,
)


def construir_grafo(herramientas, checkpointer=None):
    async def interpretar(estado: Estado) -> dict:
        texto = estado["messages"][-1].content
        interpretacion = await llm.interpretar(estado)
        if texto.strip() in MENU_INTENCION:
            interpretacion.intencion = MENU_INTENCION[texto.strip()]
        if PELIGRO.search(texto):
            interpretacion.intencion = "seguridad"
        datos = dict(estado.get("datos") or {})
        for campo in ("email", "pedido_id", "ciudad"):
            valor = getattr(interpretacion, campo)
            if valor:
                datos[campo] = (
                    valor.strip().upper() if campo == "pedido_id" else valor.strip()
                )
        # El motivo de una cita solo se acepta si es claramente una revisión o una avería.
        # Lo miramos en el texto del cliente, no en lo que deduce el modelo.
        if re.search(r"revis", texto, re.IGNORECASE):
            datos["motivo"] = "revisión"
        elif re.search(
            r"aver[ií]a|no funciona|no enciende|roto|rota|ruido|falla",
            texto,
            re.IGNORECASE,
        ):
            datos["motivo"] = "avería"
        cambios = {
            "ultima": interpretacion.model_dump(),
            "idioma": interpretacion.idioma or estado.get("idioma", "es"),
            "datos": datos,
        }
        nueva_intencion = interpretacion.intencion
        if nueva_intencion in (
            "pedido",
            "devolucion",
            "cita",
            "informacion",
        ) and nueva_intencion != estado.get("intencion"):
            # Cambio de tema: empezamos el flujo nuevo con los datos de este mensaje.
            cambios.update(fin_de_flujo())
            cambios["datos"] = {
                campo_dato: valor_dato
                for campo_dato, valor_dato in datos.items()
                if getattr(interpretacion, campo_dato, None) or campo_dato == "motivo"
            }
            cambios["intencion"] = nueva_intencion
        elif nueva_intencion not in ("continuar", "no_entendido"):
            cambios["intencion"] = nueva_intencion
        if nueva_intencion != "no_entendido":
            cambios["intentos_fallidos"] = (
                0
                if nueva_intencion != "continuar"
                else estado.get("intentos_fallidos", 0)
            )
        return cambios

    def ruta(estado: Estado) -> str:
        intencion_mensaje = estado["ultima"]["intencion"]  # lo que pide ESTE mensaje
        intencion_en_curso = estado.get("intencion")  # lo que estaba en marcha
        if intencion_en_curso == "seguridad" or intencion_mensaje == "seguridad":
            return "escalar"
        if estado.get("escalado"):
            return "ya_escalado"
        if intencion_en_curso == "persona":
            return "escalar"
        if intencion_mensaje == "no_entendido":
            # Si un flujo está esperando un dato, que repare él: sabe qué opciones volver a ofrecer.
            en_flujo = (
                intencion_en_curso in FLUJOS
                and estado.get("cliente")
                and estado.get("pendiente")
            )
            return "flujo" if en_flujo else "reparar"
        if intencion_en_curso in FLUJOS:
            return "flujo" if estado.get("cliente") else "identificar"
        if intencion_en_curso == "informacion":
            return "informar"
        return "saludar"

    async def reparar(estado: Estado) -> dict:
        intentos = estado.get("intentos_fallidos", 0) + 1
        if intentos >= MAX_INTENTOS:
            return {"intentos_fallidos": intentos, "intencion": "persona"}
        if intentos == 1:
            borrador_respuesta = borrador(
                "Dile que no le has entendido bien y pídele que te lo cuente de otra forma. "
                "Recuérdale brevemente en qué puedes ayudarle.",
                opciones=MENU,
            )
        else:
            borrador_respuesta = borrador(
                "Dile que sigues sin entenderle y pídele que elija una de las opciones. "
                "Si ninguna encaja, que pulse la de hablar con una persona.",
                opciones=MENU,
            )
        return {"intentos_fallidos": intentos, "borrador": borrador_respuesta}

    async def identificar(estado: Estado) -> dict:
        datos = estado.get("datos") or {}
        email, pedido_id = datos.get("email"), datos.get("pedido_id")
        if not email:
            pide = "su email de compra" + (
                " para comprobar que el pedido es suyo" if pedido_id else ""
            )
            return {
                "pendiente": "email",
                "borrador": borrador(
                    f"Para ayudarle necesitas identificarle: pídele {pide}."
                ),
            }
        resultado = await herramientas.llamar("buscar_cliente", email=email)
        if not resultado.get("encontrado"):
            intentos = estado.get("intentos_fallidos", 0) + 1
            if intentos >= MAX_INTENTOS:
                return {"intentos_fallidos": intentos, "intencion": "persona"}
            return {
                "intentos_fallidos": intentos,
                "datos": {**datos, "email": None},
                "pendiente": "email",
                "borrador": borrador(
                    "Dile que no encuentras ninguna compra con ese email y pídele que lo "
                    "revise o que te dé el email con el que hizo la compra."
                ),
            }
        cliente = {**resultado["cliente"], "pedidos": resultado["pedidos"]}
        return {"cliente": cliente, "pendiente": None, "intentos_fallidos": 0}

    async def flujo(estado: Estado) -> dict:
        funcion_flujo = {
            "pedido": flujo_pedido,
            "devolucion": flujo_devolucion,
            "cita": flujo_cita,
        }[estado["intencion"]]
        return await funcion_flujo(estado, herramientas)

    async def informar(estado: Estado) -> dict:
        resultado = await herramientas.llamar(
            "buscar_conocimiento", pregunta=estado["messages"][-1].content
        )
        cambios = {"intencion": None, "pendiente": None}
        if not resultado.get("resultados"):
            return {
                **cambios,
                "borrador": borrador(
                    "Dile que no tienes información fiable sobre eso y ofrécele pasarle con una persona.",
                    opciones=["Hablar con una persona", "Otra consulta"],
                ),
            }
        return {
            **cambios,
            "borrador": borrador(
                "Responde a su pregunta usando solo la información de estos fragmentos, en 2 o 3 frases. "
                "Si no responden del todo a la pregunta, dilo.",
                {"fragmentos": resultado["resultados"]},
            ),
        }

    async def saludar(estado: Estado) -> dict:
        nombre = (estado.get("cliente") or {}).get("nombre")
        return {
            "intencion": None,
            "pendiente": None,
            "borrador": borrador(
                "Saluda o responde al agradecimiento, recuerda que eres el asistente virtual de Ondo (una IA) y "
                "pregunta en qué puedes ayudarle.",
                {"nombre_cliente": nombre},
                MENU[:3],
            ),
        }

    async def escalar(estado: Estado) -> dict:
        seguridad = (
            estado.get("intencion") == "seguridad"
            or estado["ultima"]["intencion"] == "seguridad"
        )
        if seguridad:
            motivo = "seguridad"
        elif (estado.get("datos") or {}).get("motivo_escalado"):
            motivo = estado["datos"]["motivo_escalado"]
        elif estado["ultima"]["intencion"] == "persona":
            motivo = "el cliente pide hablar con una persona"
        else:
            motivo = "el asistente no consigue resolver la consulta"
        resumen = await llm.resumir(estado, motivo)
        cliente = estado.get("cliente") or {}
        resultado = await herramientas.llamar(
            "escalar_a_humano",
            motivo=motivo,
            resumen=resumen,
            prioridad="urgente" if seguridad else "normal",
            cliente_id=cliente.get("id"),
        )
        if seguridad:
            borrador_respuesta = borrador(
                "Es un caso de seguridad. Pídele que deje de usar la bicicleta y no cargue la batería, que "
                "desconecte el cargador y deje la batería en un lugar exterior lejos de materiales inflamables si "
                "puede hacerlo sin riesgo, y que si hay humo o fuego se aleje y llame al 112. Dile que una persona "
                "de Ondo le llamará por teléfono con prioridad y dale el número de caso.",
                {"caso": resultado["caso"]["id"], "espera": resultado["espera"]},
            )
        else:
            borrador_respuesta = borrador(
                "Dile que pasas su consulta a una persona del equipo y, en pocas palabras, por qué "
                "(motivo). Dile que no tendrá que repetir nada, cuándo le atenderán y su número de caso.",
                {
                    "motivo": motivo,
                    "caso": resultado["caso"]["id"],
                    "espera": resultado["espera"],
                },
            )
        return {
            "escalado": resultado["caso"],
            "intencion": None,
            "pendiente": None,
            "borrador": borrador_respuesta,
        }

    async def ya_escalado(estado: Estado) -> dict:
        return {
            "borrador": borrador(
                "Recuérdale que su consulta ya está en manos de una persona del equipo y su número de caso. "
                "Si quiere añadir algo, que lo escriba y se lo harás llegar.",
                {"caso": estado["escalado"]},
            )
        }

    async def redactar(estado: Estado) -> dict:
        borrador_respuesta = estado.get("borrador") or borrador(
            "Pregunta en qué puedes ayudarle."
        )
        respuesta = await llm.redactar(estado, borrador_respuesta)
        opciones_borrador = borrador_respuesta.get("opciones") or []
        # Si el modelo no devuelve el mismo número de botones, nos quedamos con los originales.
        opciones = (
            respuesta.opciones
            if len(respuesta.opciones) == len(opciones_borrador)
            else opciones_borrador
        )
        return {
            "messages": [AIMessage(respuesta.texto)],
            "opciones": opciones,
            "borrador": {},
        }

    def tras_nodo(estado: Estado) -> str:
        return (
            "escalar"
            if estado.get("intencion") == "persona" and not estado.get("escalado")
            else "redactar"
        )

    def tras_identificar(estado: Estado) -> str:
        if estado.get("intencion") == "persona":
            return "escalar"
        return "flujo" if estado.get("cliente") else "redactar"

    grafo = StateGraph(Estado)
    for nombre, funcion in [
        ("interpretar", interpretar),
        ("reparar", reparar),
        ("identificar", identificar),
        ("flujo", flujo),
        ("informar", informar),
        ("saludar", saludar),
        ("escalar", escalar),
        ("ya_escalado", ya_escalado),
        ("redactar", redactar),
    ]:
        grafo.add_node(nombre, funcion)
    grafo.add_edge(START, "interpretar")
    grafo.add_conditional_edges(
        "interpretar",
        ruta,
        [
            "escalar",
            "ya_escalado",
            "reparar",
            "flujo",
            "identificar",
            "informar",
            "saludar",
        ],
    )
    grafo.add_conditional_edges("reparar", tras_nodo, ["escalar", "redactar"])
    grafo.add_conditional_edges(
        "identificar", tras_identificar, ["flujo", "redactar", "escalar"]
    )
    grafo.add_conditional_edges("flujo", tras_nodo, ["escalar", "redactar"])
    for nodo in ("informar", "saludar", "escalar", "ya_escalado"):
        grafo.add_edge(nodo, "redactar")
    grafo.add_edge("redactar", END)
    return grafo.compile(checkpointer=checkpointer)
