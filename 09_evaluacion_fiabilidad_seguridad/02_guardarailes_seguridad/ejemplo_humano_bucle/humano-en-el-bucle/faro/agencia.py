"""Datos simulados de Faro Digital, una agencia de marketing para pymes.

Todo es inventado: clientes, tarifas y personas. Nada sale de tu ordenador.
"""

AGENCIA = "Faro Digital"

# Hasta este importe, el equipo de agentes puede proponer un plan sin que nadie lo apruebe.
# Por encima, lo tiene que aprobar la responsable de cuenta.
LIMITE_AUTONOMIA = 1000

PERSONAS = {
    "laura": {"nombre": "Laura Méndez", "rol": "Responsable de cuenta", "email": "laura@farodigital.test"},
    # Si Laura no responde a tiempo, la tarea se escala a Carmen (demo 4)
    "carmen": {"nombre": "Carmen Ibáñez", "rol": "Directora de cuentas", "email": "carmen@farodigital.test"},
}
PERSONA_POR_DEFECTO = "laura"

CLIENTES = {
    "obrador-espiga": {
        "nombre": "Obrador Espiga",
        "sector": "Panadería y pastelería artesana",
        "ciudad": "Valencia",
        "tiendas": 2,
        "contacto": {"web": "obradorespiga.test", "instagram": "@obradorespiga", "telefono": "960 000 111"},
        "publico_habitual": "Familias del barrio y personas que buscan productos sin gluten",
        "campanas_anteriores": [
            {"canal": "instagram_ads", "importe": 400, "resultado": "Buena interacción, pocas ventas medibles"},
            {"canal": "google_ads_local", "importe": 300, "resultado": "Muchas llamadas para reservar"},
        ],
        "brief": ("Obrador Espiga lanza su primer roscón de Reyes sin gluten. Quiere una campaña en redes y en "
                  "búsqueda local para que la gente lo reserve antes del 5 de enero. Presupuesto orientativo: "
                  "unos 1.500 €. El precio y la fecha de apertura de reservas están por confirmar."),
        # Lo que solo sabe el cliente: el equipo de agentes no lo puede averiguar con sus herramientas
        "pendiente_de_confirmar": ["Precio de venta del roscón sin gluten",
                                   "Fecha en la que se abren las reservas",
                                   "Enlace a las fotos del producto"],
    },
    "taller-radios": {
        "nombre": "Taller Radios",
        "sector": "Taller y tienda de bicicletas",
        "ciudad": "Bilbao",
        "tiendas": 1,
        "contacto": {"web": "tallerradios.test", "instagram": "@tallerradios", "telefono": "944 000 222"},
        "publico_habitual": "Ciclistas urbanos y de carretera de 25 a 55 años",
        "campanas_anteriores": [
            {"canal": "email_marketing", "importe": 60, "resultado": "Un 31 % de apertura entre clientes"},
        ],
        "brief": ("Taller Radios quiere llenar su agenda de revisiones de bicicleta en enero, que es un mes flojo. "
                  "Presupuesto: 600 €. Ofrecerá un descuento en la revisión, aún por decidir."),
        "pendiente_de_confirmar": ["Descuento exacto de la revisión", "Fechas de la promoción"],
    },
}

TARIFAS = {
    "instagram_ads": {"modelo": "coste por mil impresiones", "coste": 6.5, "minimo": 150,
                      "adecuado_para": "producto visual, público local de 25 a 45 años"},
    "facebook_ads": {"modelo": "coste por mil impresiones", "coste": 5.0, "minimo": 100,
                     "adecuado_para": "familias y público de más de 35 años"},
    "google_ads_local": {"modelo": "coste por clic", "coste": 0.6, "minimo": 150,
                         "adecuado_para": "gente que ya busca el producto cerca de la tienda"},
    "tiktok_ads": {"modelo": "coste por mil impresiones", "coste": 4.0, "minimo": 200,
                   "adecuado_para": "público de menos de 30 años"},
    "email_marketing": {"modelo": "coste fijo por envío", "coste": 60, "minimo": 60,
                        "adecuado_para": "clientes que ya conocen la marca"},
}


def ficha_cliente(cliente_id: str) -> dict:
    cliente = CLIENTES.get(cliente_id)
    if not cliente:
        return {"error": f"No existe el cliente {cliente_id}. Clientes: {', '.join(CLIENTES)}"}
    return {k: v for k, v in cliente.items() if k != "brief"} | {"id": cliente_id}


def estimar_alcance(canal: str, importe: float) -> dict:
    tarifa = TARIFAS.get(canal)
    if not tarifa:
        return {"error": f"Canal desconocido: {canal}. Canales: {', '.join(TARIFAS)}"}
    if importe < tarifa["minimo"]:
        return {"error": f"El mínimo para {canal} es {tarifa['minimo']} €"}
    if tarifa["modelo"] == "coste por mil impresiones":
        return {"canal": canal, "importe": importe, "impresiones": round(importe / tarifa["coste"] * 1000)}
    if tarifa["modelo"] == "coste por clic":
        return {"canal": canal, "importe": importe, "clics": round(importe / tarifa["coste"])}
    return {"canal": canal, "importe": importe, "envios": round(importe / tarifa["coste"])}
