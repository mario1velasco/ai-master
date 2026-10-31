"""Visión: un VLM lee una imagen, devuelve campos definidos y el código los comprueba.

La secuencia (la de la práctica):
    1. pregunta libre      el VLM describe la imagen en prosa (útil para una persona, no para el código)
    2. extracción          el mismo VLM, obligado a responder con un esquema JSON (format de Ollama)
    3. validación          Pydantic comprueba la ESTRUCTURA: campos, tipos y formatos
    4. coherencia          el código revisa el documento consigo mismo (líneas que suman el total…)
    5. consulta            el código busca el pedido / el stock en los registros (SQL con parámetros)
    6. comparación         campo a campo, en código; el veredicto y su explicación también los escribe el código

Tres cosas que este módulo nunca hace:
    - rellenar un campo que no se lee (se deja null y se apunta en campos_ilegibles);
    - tratar la «legibilidad» que declara el modelo como una probabilidad (no está calibrada);
    - decir por qué hay una discrepancia (fraude, error de una persona…): eso exige revisar.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import time
from datetime import date
from typing import Literal

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, ValidationError

from . import config, datos
from .ollama import ErrorComponente, chat

TIPOS = ("ticket", "recuento", "albaran")

# ---------------------------------------------------------------------------
# Esquemas: los campos que queremos, con su tipo. null = no se lee o no aparece.
# ---------------------------------------------------------------------------


class LineaTicket(BaseModel):
    producto: str | None = Field(None, description="Nombre del producto tal como aparece (p. ej. NIGHT SHIFT)")
    sku: str | None = Field(None, description="Código de producto en mayúsculas con guiones bajos (p. ej. NIGHT_SHIFT_LILA_41)")
    linea_id: str | None = Field(None, description="Identificador de la línea tras «LÍNEA:»")
    cantidad: int | None = Field(None, description="Unidades de la línea")
    precio_unitario: float | None = Field(None, description="Precio por unidad en euros")
    descuento: float | None = Field(None, description="Descuento de la línea en euros")
    importe: float | None = Field(None, description="Importe de la línea en euros, tal como está impreso")


class Ticket(BaseModel):
    pedido_id: str | None = Field(None, description="Número de pedido tras «PEDIDO:»")
    fecha: date | None = Field(None, description="Fecha de compra en formato AAAA-MM-DD")
    tienda_codigo: str | None = Field(None, description="Código de tienda de tres letras y tres letras (p. ej. MAD-MAL)")
    lineas: list[LineaTicket] = Field(default_factory=list, description="Una entrada por producto")
    total_impreso: float | None = Field(None, description="El TOTAL impreso, en euros, aunque no cuadre con las líneas")
    texto_campana: str | None = Field(None, description="Texto de una campaña o promoción impresa; null si no hay ninguna")
    campos_ilegibles: list[str] = Field(default_factory=list, description="Nombres de los campos que no se pueden leer")
    legibilidad_declarada: Literal["buena", "regular", "mala"] = Field(
        "buena", description="Cómo de legible te parece la imagen (opinión del modelo, no una probabilidad)")


class FilaRecuento(BaseModel):
    sku: str | None = Field(None, description="Código de producto")
    unidades: int | None = Field(None, description="Unidades anotadas")


class Recuento(BaseModel):
    tienda: str | None = Field(None, description="Tienda de la cabecera (p. ej. Malasaña o MAD-MAL)")
    fecha: date | None = Field(None, description="Fecha del recuento en formato AAAA-MM-DD")
    hora: str | None = Field(None, description="Hora del recuento en formato HH:MM")
    filas: list[FilaRecuento] = Field(default_factory=list)
    campos_ilegibles: list[str] = Field(default_factory=list)
    legibilidad_declarada: Literal["buena", "regular", "mala"] = "buena"


class LineaAlbaran(BaseModel):
    sku: str | None = None
    unidades_previstas: int | None = Field(None, description="Columna «UD PREVISTAS»")


class Albaran(BaseModel):
    albaran_id: str | None = Field(None, description="Código del albarán (p. ej. DL-0604-MAL)")
    tienda_codigo: str | None = Field(None, description="Código de la tienda de destino (p. ej. MAD-MAL)")
    fecha_programada: date | None = Field(None, description="Fecha programada en formato AAAA-MM-DD")
    estado_entrega: str | None = Field(None, description="Estado de la entrega tal como aparece")
    incidencia: str | None = Field(None, description="Incidencia o motivo, si aparece")
    recepcion_realizada: bool | None = Field(None, description="true si dice que se recibió; false si dice que no; null si no lo dice")
    lineas: list[LineaAlbaran] = Field(default_factory=list)
    campos_ilegibles: list[str] = Field(default_factory=list)
    legibilidad_declarada: Literal["buena", "regular", "mala"] = "buena"


ESQUEMAS: dict[str, type[BaseModel]] = {"ticket": Ticket, "recuento": Recuento, "albaran": Albaran}

INSTRUCCIONES = {
    "ticket": "Es un justificante de compra de una tienda DropLab.",
    "recuento": "Es una hoja de recuento de stock de una tienda DropLab.",
    "albaran": "Es un albarán de reparto a una tienda DropLab.",
}

REGLAS_EXTRACCION = """Extrae los campos de la imagen y responde SOLO con un JSON que siga este esquema.
Reglas:
- Copia los valores tal como aparecen impresos. No calcules, no corrijas y no completes nada.
- Si un total no cuadra con las líneas, copia el total impreso igualmente.
- Si un campo no aparece o no se puede leer, pon null y añade su nombre a campos_ilegibles.
- Importes con punto decimal (231.99), fechas AAAA-MM-DD.
- Escribe el JSON compacto, en una sola línea, sin espacios ni saltos de línea.
Esquema:
"""

# ---------------------------------------------------------------------------
# Imagen
# ---------------------------------------------------------------------------


class ImagenPreparada(BaseModel):
    b64: str
    sha256: str
    ancho: int
    alto: int
    ancho_original: int
    alto_original: int
    formato: str


def preparar_imagen(contenido: bytes, max_lado: int = config.MAX_LADO_IMAGEN) -> ImagenPreparada:
    """Comprueba que es una imagen, la reduce a max_lado px y la pasa a PNG en base64 (lo que espera Ollama)."""
    if not contenido:
        raise ErrorComponente("IMAGEN_VACIA", "vision", "No ha llegado ninguna imagen (0 bytes).")
    if len(contenido) > config.MAX_BYTES_IMAGEN:
        raise ErrorComponente("IMAGEN_DEMASIADO_GRANDE", "vision", f"La imagen ocupa {len(contenido) / 1e6:.1f} MB (máximo 15).")
    try:
        im = Image.open(io.BytesIO(contenido))
        formato = im.format or "?"
        im = im.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ErrorComponente("IMAGEN_NO_VALIDA", "vision", "El archivo recibido no es una imagen que se pueda abrir.")
    w0, h0 = im.size
    im.thumbnail((max_lado, max_lado))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return ImagenPreparada(b64=base64.b64encode(buf.getvalue()).decode(), sha256=hashlib.sha256(contenido).hexdigest(),
                           ancho=im.size[0], alto=im.size[1], ancho_original=w0, alto_original=h0, formato=formato)


def desde_data_uri(uri: str) -> bytes:
    """«data:image/png;base64,iVBOR…» → bytes. Es como llegan las imágenes desde Open WebUI."""
    m = re.match(r"^data:image/[\w.+-]+;base64,(.+)$", uri or "", re.S)
    try:
        return base64.b64decode(m[1] if m else uri, validate=False)
    except Exception:  # noqa: BLE001
        raise ErrorComponente("IMAGEN_NO_VALIDA", "vision", "La imagen no está en base64 válido.")


# ---------------------------------------------------------------------------
# 1. Pregunta libre · 2. Extracción · 3. Validación
# ---------------------------------------------------------------------------


def pregunta_libre(img: ImagenPreparada, pregunta: str = "¿Qué es este documento y qué dice? Responde en español, en 3 frases.",
                   modelo: str | None = None) -> dict:
    r = chat(modelo or config.MODELO_VISION, [{"role": "user", "content": pregunta, "images": [img.b64]}],
             num_ctx=config.CTX_VISION, num_predict=300)
    return {"respuesta": r.contenido.strip(), "tiempos": r.tiempos()}


def clasificar(img: ImagenPreparada, modelo: str | None = None) -> dict:
    """¿Ticket, recuento o albarán? Una salida de una sola palabra, también con esquema (enum)."""
    esquema = {"type": "object", "properties": {"tipo": {"type": "string", "enum": [*TIPOS, "otro"]}}, "required": ["tipo"]}
    r = chat(modelo or config.MODELO_VISION, [{"role": "user", "images": [img.b64], "content":
             "¿Qué tipo de documento es? ticket = justificante de compra; recuento = hoja de recuento de stock; "
             "albaran = albarán de reparto; otro = cualquier otra cosa. Responde en JSON."}],
             formato=esquema, num_ctx=config.CTX_VISION, num_predict=20)
    try:
        tipo = json.loads(r.contenido)["tipo"]
    except (json.JSONDecodeError, KeyError):
        tipo = "otro"
    return {"tipo": tipo if tipo in (*TIPOS, "otro") else "otro", "tiempos": r.tiempos()}


def prompt_extraccion(tipo: str) -> str:
    return (INSTRUCCIONES[tipo] + "\n" + REGLAS_EXTRACCION
            + json.dumps(ESQUEMAS[tipo].model_json_schema(), ensure_ascii=False))


def validar(tipo: str, json_crudo: str) -> tuple[dict | None, list[dict]]:
    """Pydantic: ¿es JSON? ¿Están los campos con su tipo? Devuelve los datos limpios o la lista de errores."""
    try:
        obj = ESQUEMAS[tipo].model_validate_json(json_crudo)
    except ValidationError as exc:
        return None, [{"campo": ".".join(str(x) for x in e["loc"]) or "(todo)", "error": e["msg"]} for e in exc.errors()]
    return json.loads(obj.model_dump_json()), []


_CACHE: dict[tuple, dict] = {}


def extraer(img: ImagenPreparada, tipo: str, modelo: str | None = None, con_esquema: bool = True,
            usar_cache: bool = False) -> dict:
    """El VLM extrae los campos. con_esquema=False: sin «format» (para ver qué pasa sin él)."""
    if tipo not in ESQUEMAS:
        raise ErrorComponente("TIPO_NO_VALIDO", "vision", f"Tipo de documento {tipo!r}: usa {', '.join(TIPOS)}.")
    modelo = modelo or config.MODELO_VISION
    clave = (img.sha256, tipo, modelo, con_esquema)
    disco = config.GUARDADAS / "cache_vision" / f"{img.sha256[:16]}_{tipo}_{modelo.replace(':', '_')}.json"
    if usar_cache and clave in _CACHE:
        return {**_CACHE[clave], "reutilizada": True}
    if usar_cache and con_esquema and disco.exists():     # misma imagen (huella sha256), mismo tipo y modelo
        _CACHE[clave] = json.loads(disco.read_text(encoding="utf-8"))
        return {**_CACHE[clave], "reutilizada": True}
    esquema = ESQUEMAS[tipo].model_json_schema()
    r = chat(modelo, [{"role": "user", "content": prompt_extraccion(tipo), "images": [img.b64]}],
             formato=esquema if con_esquema else None, num_ctx=config.CTX_VISION, num_predict=900)
    crudo = r.contenido.strip()
    if not con_esquema:                      # sin esquema suele venir con ```json … ```: lo quitamos para validar
        crudo = re.sub(r"^```(?:json)?\s*|\s*```$", "", crudo)
    datos_, errores = validar(tipo, crudo)
    res = {"tipo": tipo, "modelo": modelo, "json_crudo": crudo, "valido": not errores, "errores_validacion": errores,
           "datos": datos_, "tiempos": r.tiempos(), "imagen": {"sha256": img.sha256[:12], "px": f"{img.ancho}×{img.alto}",
                                                               "px_original": f"{img.ancho_original}×{img.alto_original}"},
           "reutilizada": False}
    if not errores:
        _CACHE[clave] = res
        if con_esquema:
            disco.parent.mkdir(parents=True, exist_ok=True)
            disco.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res


# ---------------------------------------------------------------------------
# 4. Coherencia del documento consigo mismo (sin mirar los registros)
# ---------------------------------------------------------------------------


def _c(campo, en_imagen, en_registro, resultado, nota="", clase="registro"):
    """Una comprobación. clase: formato (¿es un valor posible?), coherencia (¿cuadra consigo mismo?)
    o registro (¿coincide con caja o con el stock?)."""
    return {"campo": campo, "en_imagen": en_imagen, "en_registro": en_registro, "resultado": resultado, "nota": nota,
            "clase": clase}


def eur(x) -> str:
    return "—" if x is None else f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


LINEA_RE = re.compile(r"^[AB]-(?:MAD-MAL|MAD-GOY|BCN-EIX)-\d{4}$")
PERIODO_DATOS = (date(2026, 3, 2), date(2026, 4, 26))


def formato_ticket(t: dict) -> list[dict]:
    """¿Son valores POSIBLES? Un valor imposible delata un error de lectura antes de mirar los registros."""
    out = []
    pid = t.get("pedido_id")
    if pid and not datos.PEDIDO_RE.fullmatch(pid.upper()):
        out.append(_c("formato del pedido", pid, "A|B-TIENDA-ORD-0000", "aviso",
                      "No es un número de pedido posible: probable error de lectura.", "formato"))
    if t.get("fecha"):
        f = date.fromisoformat(t["fecha"])
        if not PERIODO_DATOS[0] <= f <= PERIODO_DATOS[1]:
            out.append(_c("fecha dentro de los datos", t["fecha"], "02/03–26/04/2026", "aviso",
                          "Fecha fuera del periodo con datos: probable error de lectura.", "formato"))
    if t.get("tienda_codigo") and t["tienda_codigo"].upper() not in datos.TIENDAS:
        out.append(_c("código de tienda", t["tienda_codigo"], ", ".join(datos.TIENDAS), "aviso",
                      "No es un código de tienda de DropLab.", "formato"))
    skus = {r[0] for r in datos.conexion().cursor().execute("SELECT sku FROM catalogo").fetchall()}
    for i, l in enumerate(t.get("lineas") or [], 1):
        if l.get("linea_id") and not LINEA_RE.fullmatch(l["linea_id"].upper()):
            out.append(_c(f"línea {i}: formato", l["linea_id"], "A|B-TIENDA-0000", "aviso",
                          "No es un identificador de línea posible.", "formato"))
        if l.get("sku") and l["sku"].upper() not in skus:
            out.append(_c(f"línea {i}: SKU en el catálogo", l["sku"], "no está en el catálogo", "aviso",
                          "Ese producto no existe en el catálogo.", "formato"))
    return out


def coherencia_ticket(t: dict) -> list[dict]:
    """¿Cuadran las cuentas DENTRO del ticket? cantidad × precio − descuento = importe; Σ importes = total."""
    out = formato_ticket(t)
    for i, l in enumerate(t.get("lineas") or [], 1):
        if None in (l.get("cantidad"), l.get("precio_unitario"), l.get("descuento"), l.get("importe")):
            out.append(_c(f"línea {i}: cuenta", "faltan datos", None, "sin_dato", "No se puede recalcular la línea.",
                          "coherencia"))
            continue
        calc = round(l["cantidad"] * l["precio_unitario"] - l["descuento"], 2)
        ok = abs(calc - l["importe"]) <= 0.01
        out.append(_c(f"línea {i}: cantidad × precio − descuento", eur(l["importe"]), eur(calc),
                      "coincide" if ok else "no_coincide", "" if ok else "La línea impresa no cuadra con su propia cuenta.",
                      "coherencia"))
    importes = [l.get("importe") for l in t.get("lineas") or []]
    if importes and None not in importes and t.get("total_impreso") is not None:
        suma = round(sum(importes), 2)
        ok = abs(suma - t["total_impreso"]) <= 0.01
        out.append(_c("total impreso = suma de sus líneas", eur(t["total_impreso"]), eur(suma),
                      "coincide" if ok else "no_coincide",
                      "" if ok else f"El ticket no cuadra consigo mismo: diferencia de {eur(abs(suma - t['total_impreso']))}.",
                      "coherencia"))
    return out


# ---------------------------------------------------------------------------
# 5–6. Consulta de los registros y comparación (código, no modelo)
# ---------------------------------------------------------------------------


def comprobar_ticket(t: dict) -> dict:
    """El ticket (lo que se lee) frente a caja (ventas.csv, por la capa semántica)."""
    comprobaciones = coherencia_ticket(t)
    consultas = []
    pid = (t.get("pedido_id") or "").strip().upper()
    if not pid:
        return _veredicto("ticket", comprobaciones + [_c("pedido", None, None, "sin_dato", "No se lee el número de pedido.")],
                          consultas)
    try:
        caja = datos.pedido(pid)
    except ErrorComponente as e:
        return _veredicto("ticket", comprobaciones + [_c("pedido", pid, None, "sin_dato", e.mensaje)], consultas)
    consultas.append({k: caja[k] for k in ("herramienta", "titulo", "sql", "parametros", "filas")})
    consultas.append({k: caja["abonos"][k] for k in ("herramienta", "titulo", "sql", "parametros", "filas")})
    filas = caja["filas"]
    if not filas:
        return _veredicto("ticket", comprobaciones + [_c("pedido", pid, "no existe en caja", "no_coincide",
                                                          "El pedido impreso no aparece en los registros.")], consultas)
    f0 = filas[0]
    comprobaciones.append(_c("pedido", pid, pid, "coincide"))
    if t.get("fecha"):
        comprobaciones.append(_c("fecha", t["fecha"], f0["fecha_venta"], "coincide" if t["fecha"] == f0["fecha_venta"] else "no_coincide"))
    else:
        comprobaciones.append(_c("fecha", None, f0["fecha_venta"], "sin_dato", "No se lee la fecha."))
    tienda = (t.get("tienda_codigo") or "").upper()
    comprobaciones.append(_c("tienda", t.get("tienda_codigo"), f0["local_id"],
                             "coincide" if tienda == f0["local_id"] else ("sin_dato" if not tienda else "no_coincide"),
                             "" if tienda else "No se lee el código de tienda."))
    por_linea = {f["linea_id"]: f for f in filas}
    por_sku = {f["sku"]: f for f in filas}
    vistas = set()
    for i, l in enumerate(t.get("lineas") or [], 1):
        reg = por_linea.get((l.get("linea_id") or "").upper()) or por_sku.get((l.get("sku") or "").upper())
        if not reg:
            comprobaciones.append(_c(f"línea {i}", l.get("linea_id") or l.get("sku"), None, "no_coincide",
                                     "Esta línea no aparece en el pedido de caja."))
            continue
        vistas.add(reg["linea_id"])
        for campo, clave in (("cantidad", "cantidad"), ("importe", "importe")):
            v = l.get(campo)
            if v is None:
                comprobaciones.append(_c(f"línea {i}: {campo}", None, reg[clave], "sin_dato"))
            else:
                ok = abs(float(v) - float(reg[clave])) <= 0.01
                comprobaciones.append(_c(f"línea {i} ({reg['sku']}): {campo}", eur(v) if campo == "importe" else v,
                                         eur(reg[clave]) if campo == "importe" else reg[clave], "coincide" if ok else "no_coincide"))
    for lid in set(por_linea) - vistas:
        comprobaciones.append(_c("línea de caja", None, lid, "no_coincide", "Caja tiene una línea que no se ve en el ticket."))
    if t.get("total_impreso") is None:
        comprobaciones.append(_c("total", None, eur(caja["total"]), "sin_dato", "No se lee el total."))
    else:
        dif = round(t["total_impreso"] - caja["total"], 2)
        comprobaciones.append(_c("total: impreso frente a caja", eur(t["total_impreso"]), eur(caja["total"]),
                                 "coincide" if abs(dif) <= 0.01 else "no_coincide",
                                 "" if abs(dif) <= 0.01 else f"Diferencia de {eur(abs(dif))}."))
    abonos = caja["abonos"]["filas"]
    contexto = []
    if abonos:
        abonado = round(sum(a["importe_abonado"] for a in abonos), 2)
        frase = (f"Después de la venta constan {len(abonos)} abono(s) de este pedido por {eur(abonado)} ("
                 + "; ".join(f"{a['linea_id']} el {a['fecha_reconocimiento']}, {a['motivo']}" for a in abonos) + "). ")
        if t.get("total_impreso") is not None and abs(t["total_impreso"] - caja["total"]) > 0.01:
            frase += (f"Los abonos NO explican la diferencia del total: se calculan sobre el importe de caja "
                      f"({eur(caja['total'])}), no sobre el impreso.")
        else:
            frase += "No cambian lo que dice el ticket, pero sí el neto de esa venta."
        contexto.append(frase)
    return _veredicto("ticket", comprobaciones, consultas, contexto)


def comprobar_recuento(r: dict, local_id: str = "MAD-MAL") -> dict:
    """La hoja de recuento frente al registro de disponibilidad, en el mismo SKU, tienda y momento."""
    comprobaciones, consultas = [], []
    leida = (r.get("tienda") or "").strip()
    if leida and leida.upper() != local_id and leida.lower() != datos.TIENDAS[local_id].lower():
        comprobaciones.append(_c("tienda", leida, local_id, "aviso",
                                 f"«{leida}» no es una tienda: probable error de LECTURA, no del recuento. "
                                 f"Se compara con {local_id}.", "lectura"))
    if not (r.get("fecha") and r.get("hora")):
        return _veredicto("recuento", [_c("momento", None, None, "sin_dato", "No se lee la fecha o la hora del recuento.")], [])
    skus = [f["sku"] for f in r.get("filas") or [] if f.get("sku")]
    reg = datos.disponibilidad_en(local_id, f"{r['fecha']} {r['hora']}", skus)
    consultas.append(reg)
    por_sku = {f["sku"]: f for f in reg["filas"]}
    for f in r.get("filas") or []:
        g = por_sku.get(f.get("sku"))
        if g is None:
            comprobaciones.append(_c(f.get("sku") or "?", f.get("unidades"), None, "sin_dato", "Sin registro para ese SKU y momento."))
        elif f.get("unidades") is None:
            comprobaciones.append(_c(f["sku"], None, g["unidades_disponibles"], "sin_dato", "No se leen las unidades."))
        else:
            ok = f["unidades"] == g["unidades_disponibles"]
            comprobaciones.append(_c(f["sku"], f["unidades"], g["unidades_disponibles"], "coincide" if ok else "no_coincide",
                                     "" if ok else "La hoja y el registro no coinciden en el mismo momento."))
    contexto = ["El registro de disponibilidad no concilia todos los movimientos (ventas, ajustes, mermas): una "
                "diferencia no permite atribuir un error a una persona."]
    return _veredicto("recuento", comprobaciones, consultas, contexto)


def comprobar_albaran(a: dict) -> dict:
    """El albarán dice lo PREVISTO. Se contrasta con los huecos de stock de ese día; nunca se suma como recibido."""
    comprobaciones, consultas, contexto = [], [], []
    if a.get("recepcion_realizada") is False:
        comprobaciones.append(_c("recepción", "no realizada", None, "aviso",
                                 "Unidades previstas ≠ unidades recibidas: este albarán no añade stock."))
    elif a.get("recepcion_realizada") is None:
        comprobaciones.append(_c("recepción", None, None, "sin_dato", "El albarán no dice si se recibió."))
    local = (a.get("tienda_codigo") or "MAD-MAL").upper()
    if a.get("fecha_programada") and local in datos.TIENDAS:
        rot = datos.roturas_dia(local, a["fecha_programada"])
        consultas.append(rot)
        sin_stock = {f["sku"]: f for f in rot["filas"]}
        for l in a.get("lineas") or []:
            g = sin_stock.get(l.get("sku"))
            comprobaciones.append(_c(f"{l.get('sku')}: previstas {l.get('unidades_previstas')}", "en el albarán",
                                     f"sin stock {g['desde']}–{g['hasta']}" if g else "sin hueco registrado",
                                     "aviso" if g else "sin_dato",
                                     "Coincide en el tiempo con un hueco de stock: es compatible, no lo demuestra." if g else ""))
    contexto.append("Un albarán con unidades previstas no demuestra que se recibieran. Para saber cuándo y cómo se "
                    "repuso hay que ir al informe de logística (documentos).")
    return _veredicto("albaran", comprobaciones, consultas, contexto)


def _veredicto(tipo: str, comprobaciones: list[dict], consultas: list[dict], contexto: list[str] | None = None) -> dict:
    """El veredicto y su explicación los escribe el CÓDIGO, a partir de las comprobaciones."""
    n = {k: sum(c["resultado"] == k for c in comprobaciones) for k in ("coincide", "no_coincide", "sin_dato", "aviso")}
    formato = [c for c in comprobaciones if c.get("clase") == "formato" and c["resultado"] != "coincide"]
    if formato:
        veredicto = "lectura_dudosa"
    elif n["no_coincide"]:
        veredicto = "discrepancia"
    elif n["sin_dato"] and not n["coincide"]:
        veredicto = "no_verificable"
    elif n["sin_dato"]:
        veredicto = "coincide_en_parte"
    elif n["aviso"] and not n["coincide"]:
        veredicto = "revisar"
    else:
        veredicto = "coincide"
    frases = {
        "lectura_dudosa": "La extracción tiene valores imposibles ({nf}): lo más probable es un error de LECTURA. "
                          "Antes de comparar con los registros, repetir la imagen o revisarla a mano. "
                          "El modelo no lo marcó como ilegible: su «legibilidad» no es una probabilidad.",
        "discrepancia": "Hay {no_coincide} discrepancia(s) entre la imagen y los registros. Una discrepancia pide "
                        "revisión: no indica por sí sola la causa ni un responsable.",
        "coincide": "Todo lo que se ha podido leer coincide con los registros ({coincide} comprobaciones). Leer bien un "
                    "documento no demuestra que el documento sea correcto; aquí, además, coincide con caja.",
        "coincide_en_parte": "Lo legible coincide ({coincide}), pero {sin_dato} campo(s) no se han podido comprobar.",
        "no_verificable": "No hay datos suficientes para comprobarlo ({sin_dato} sin dato).",
        "revisar": "No hay contradicciones, pero sí {aviso} aviso(s) que conviene leer.",
    }
    explicacion = [frases[veredicto].format(nf=len(formato), **n)] + list(contexto or [])
    vistas = set()
    for c in comprobaciones:
        if c["resultado"] in ("no_coincide", "aviso") and c["nota"] and c["nota"] not in vistas:
            vistas.add(c["nota"])
            explicacion.append(f"{c['campo']}: {c['nota']}")
    return {"tipo": tipo, "veredicto": veredicto, "recuento": n, "comprobaciones": comprobaciones,
            "consultas": consultas, "explicacion": explicacion}


COMPROBAR = {"ticket": comprobar_ticket, "recuento": comprobar_recuento, "albaran": comprobar_albaran}


def analizar_imagen(contenido: bytes, tipo: str | None = None, modelo: str | None = None, usar_cache: bool = False) -> dict:
    """Todo seguido: preparar → (clasificar) → extraer → validar → comprobar. Lo usan la API y el flujo."""
    t0 = time.time()
    img = preparar_imagen(contenido)
    pasos = []
    if tipo is None:
        cl = clasificar(img, modelo)
        tipo = cl["tipo"]
        pasos.append({"paso": "clasificar", **cl["tiempos"], "resultado": tipo})
        if tipo == "otro":
            raise ErrorComponente("DOCUMENTO_NO_RECONOCIDO", "vision",
                                  "La imagen no parece un ticket, un recuento ni un albarán de DropLab.")
    ex = extraer(img, tipo, modelo, usar_cache=usar_cache)
    pasos.append({"paso": "extraer", **ex["tiempos"], "reutilizada": ex["reutilizada"]})
    if not ex["valido"]:
        return {"tipo": tipo, "extraccion": ex, "comprobacion": None, "pasos": pasos, "segundos": round(time.time() - t0, 1)}
    comp = COMPROBAR[tipo](ex["datos"])
    return {"tipo": tipo, "extraccion": ex, "comprobacion": comp, "pasos": pasos, "segundos": round(time.time() - t0, 1)}
