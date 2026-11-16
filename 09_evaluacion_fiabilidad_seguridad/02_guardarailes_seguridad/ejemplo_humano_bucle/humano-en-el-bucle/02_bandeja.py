"""Demo 2 · La bandeja de la persona.

Una página web local donde la responsable de cuenta ve las tareas que le ha delegado el
equipo de agentes y las completa. Al responder, el MISMO equipo continúa en segundo plano
donde lo dejó; en esta terminal verás lo que hace.

Uso:  python 02_bandeja.py        y abre http://127.0.0.1:8000
"""
import html

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from faro import agencia
from faro.flujo import abrir_faro
from faro.utilidades import euros

app = FastAPI(title="Faro Digital · Bandeja de tareas")
fabrica_modelo = None   # permite usar un modelo simulado en las pruebas


def _faro(mostrar=False):
    return abrir_faro(fabrica_modelo() if fabrica_modelo else None, mostrar=mostrar)


# --- API: lo que usa la página (y cualquier otro sistema de la empresa) ----------------
class NuevoEncargo(BaseModel):
    cliente_id: str


class Respuesta(BaseModel):
    decision: str | None = None          # tarea de aprobación: aprobar, modificar o rechazar
    presupuesto: float | None = None     # si decision = modificar
    comentario: str = ""
    respuestas: dict[str, str] = {}      # tarea de datos: pregunta → respuesta


def _iniciar(cliente_id: str):
    with _faro(mostrar=True) as faro:
        faro.nuevo_encargo(cliente_id)


def _reanudar(id_encargo: str, respuesta: dict):
    with _faro(mostrar=True) as faro:
        faro.responder(id_encargo, respuesta)


@app.get("/api/encargos")
def listar():
    with _faro() as faro:
        return faro.encargos()


@app.post("/api/encargos", status_code=202)
def crear(nuevo: NuevoEncargo, segundo_plano: BackgroundTasks):
    if nuevo.cliente_id not in agencia.CLIENTES:
        raise HTTPException(404, "Cliente desconocido")
    segundo_plano.add_task(_iniciar, nuevo.cliente_id)
    return {"estado": "el equipo empieza a trabajar"}


@app.post("/api/encargos/{id_encargo}/respuesta", status_code=202)
def responder(id_encargo: str, respuesta: Respuesta, segundo_plano: BackgroundTasks):
    with _faro() as faro:
        tarea = faro.tarea_pendiente(id_encargo)
    if not tarea:
        raise HTTPException(409, "Este encargo no está esperando a ninguna persona")
    if tarea["tipo"] == "aprobacion" and respuesta.decision not in ("aprobar", "modificar", "rechazar"):
        raise HTTPException(422, "Elige aprobar, modificar o rechazar")
    if tarea["tipo"] == "datos" and not any(v.strip() for v in respuesta.respuestas.values()):
        raise HTTPException(422, "Responde al menos uno de los datos")
    if respuesta.decision == "modificar" and not respuesta.presupuesto:
        raise HTTPException(422, "Indica el presupuesto máximo que apruebas")
    # 202: aceptada. La respuesta vuelve enseguida y el equipo trabaja en segundo plano
    segundo_plano.add_task(_reanudar, id_encargo, respuesta.model_dump())
    return {"estado": "el equipo retoma el encargo"}


# --- Páginas ----------------------------------------------------------------------
ESTILO = """<style>
:root{--azul:#0b3954;--claro:#eef4f8;--borde:#d5dde3;--ambar:#b26b00;--verde:#2f7d4f;--rojo:#b23b3b}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f7f9fa;color:#1d2a33}
header{background:var(--azul);color:#fff;padding:14px 24px}header a{color:#fff;text-decoration:none}
main{max-width:900px;margin:24px auto;padding:0 16px}
.tarjeta{background:#fff;border:1px solid var(--borde);border-radius:10px;padding:18px 20px;margin-bottom:16px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--borde)}
.etiqueta{display:inline-block;padding:2px 10px;border-radius:12px;font-size:13px;color:#fff}
.esperando_persona{background:var(--ambar)}.trabajando{background:#4a6fa5}.terminado{background:var(--verde)}.error{background:var(--rojo)}
button,.boton{background:var(--azul);color:#fff;border:0;border-radius:6px;padding:9px 16px;font-size:15px;cursor:pointer;text-decoration:none}
input,textarea,select{width:100%;box-sizing:border-box;padding:8px;border:1px solid var(--borde);border-radius:6px;font:inherit;margin:4px 0 12px}
pre{white-space:pre-wrap;background:var(--claro);padding:14px;border-radius:8px;font-size:14px}
.linea{font-size:14px;padding:4px 0;border-bottom:1px dashed var(--borde)}.gris{color:#5b6b75;font-size:13px}
</style>"""

ETIQUETAS = {"esperando_persona": "Esperando a una persona", "trabajando": "El equipo está trabajando",
             "terminado": "Terminado", "error": "Error"}


def pagina(titulo: str, cuerpo: str, refrescar=False) -> HTMLResponse:
    meta = '<meta http-equiv="refresh" content="4">' if refrescar else ""
    return HTMLResponse(f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{meta}<title>{titulo}</title>{ESTILO}</head>
<body><header><a href="/"><b>Faro Digital</b> · Bandeja de tareas</a></header><main>{cuerpo}</main>
<script>
const valor = id => document.getElementById(id).value;
async function enviar(url, datos) {{
  const r = await fetch(url, {{method: "POST", headers: {{"Content-Type": "application/json"}}, body: JSON.stringify(datos)}});
  if (!r.ok) {{ alert((await r.json()).detail); return; }}
  location.reload();
}}
</script></body></html>""")


@app.get("/", response_class=HTMLResponse)
def bandeja():
    with _faro() as faro:
        encargos = faro.encargos()
        filas = ""
        for e in encargos:
            persona = agencia.PERSONAS.get(e["asignado_a"] or "", {}).get("nombre", "—")
            filas += (f"<tr><td><a href='/encargo/{e['id']}'>{e['id']}</a></td>"
                      f"<td>{agencia.CLIENTES[e['cliente_id']]['nombre']}</td>"
                      f"<td><span class='etiqueta {e['estado']}'>{ETIQUETAS[e['estado']]}</span></td>"
                      f"<td>{persona if e['estado'] == 'esperando_persona' else '—'}</td>"
                      f"<td class='gris'>{(e['esperando_desde'] or '')[11:16]}</td></tr>")
    opciones = "".join(f"<option value='{k}'>{v['nombre']}</option>" for k, v in agencia.CLIENTES.items())
    cuerpo = f"""<div class="tarjeta"><h2 style="margin-top:0">Encargos</h2>
<table><tr><th>Encargo</th><th>Cliente</th><th>Estado</th><th>Tarea para</th><th>Desde</th></tr>
{filas or "<tr><td colspan=5 class='gris'>Todavía no hay encargos. Crea uno abajo o con la demo 1.</td></tr>"}</table></div>
<div class="tarjeta"><h3 style="margin-top:0">Nuevo encargo</h3>
<select id="cliente">{opciones}</select>
<button onclick="enviar('/api/encargos', {{cliente_id: document.getElementById('cliente').value}})">Encargar al equipo</button></div>"""
    return pagina("Bandeja · Faro Digital", cuerpo, refrescar=any(e["estado"] == "trabajando" for e in encargos))


def formulario(id_encargo: str, tarea: dict) -> str:
    plan = tarea["plan"]
    filas = "".join(f"<tr><td>{c['canal']}</td><td>{euros(c['importe'])}</td><td>{html.escape(c['objetivo'])}</td></tr>"
                    for c in plan["canales"])
    resumen = (f"<p><b>Cliente:</b> {tarea['cliente']}<br><span class='gris'>{html.escape(tarea['brief'])}</span></p>"
               f"<table><tr><th>Canal</th><th>Importe</th><th>Objetivo</th></tr>{filas}"
               f"<tr><th>Total</th><th>{euros(plan['presupuesto_total'])}</th><th></th></tr></table>")
    url = f"/api/encargos/{id_encargo}/respuesta"
    if tarea["tipo"] == "aprobacion":
        campos = f"""<label>Decisión</label><select id="decision">
<option value="aprobar">Aprobar el plan</option><option value="modificar">Aprobar con otro presupuesto máximo</option>
<option value="rechazar">Rechazar y pedir otro plan</option></select>
<label>Presupuesto máximo en euros (solo si cambias el presupuesto)</label><input id="presupuesto" type="number" min="0">
<label>Comentario para el equipo</label><textarea id="comentario" rows="3"></textarea>
<button onclick="enviar('{url}', {{decision: valor('decision'), presupuesto: Number(valor('presupuesto')) || null,
comentario: valor('comentario')}})">Enviar decisión al equipo</button>"""
    else:
        preguntas = tarea["preguntas"]
        campos = "".join(f"<label>{html.escape(p)}</label><input id='p{i}'>" for i, p in enumerate(preguntas))
        datos = ", ".join(f"{p!r}: valor('p{i}')" for i, p in enumerate(preguntas))
        campos += f"<button onclick=\"enviar('{url}', {{respuestas: {{{html.escape(datos)}}}}})\">Enviar datos al equipo</button>"
    return (f"<div class='tarjeta' style='border-color:var(--ambar)'><h2 style='margin-top:0'>🙋 {html.escape(tarea['titulo'])}</h2>"
            f"<p>{html.escape(tarea['instrucciones'])}</p>{resumen}<hr style='border:0;border-top:1px solid var(--borde);margin:16px 0'>{campos}</div>")


@app.get("/encargo/{id_encargo}", response_class=HTMLResponse)
def ver_encargo(id_encargo: str):
    with _faro() as faro:
        encargo = faro.encargo(id_encargo)
        if not encargo:
            raise HTTPException(404, "No existe ese encargo")
        estado, tarea = faro.estado(id_encargo), faro.tarea_pendiente(id_encargo)
    persona = agencia.PERSONAS.get(encargo["asignado_a"] or "", {})
    cabecera = (f"<div class='tarjeta'><h2 style='margin-top:0'>{id_encargo} · "
                f"{agencia.CLIENTES[encargo['cliente_id']]['nombre']}</h2>"
                f"<span class='etiqueta {encargo['estado']}'>{ETIQUETAS[encargo['estado']]}</span>"
                + (f" <span class='gris'>· tarea para {persona['nombre']} ({persona['rol']})</span>" if tarea else "")
                + (f"<pre>{html.escape(encargo['error'] or '')}</pre>" if encargo["estado"] == "error" else "") + "</div>")
    cuerpo = cabecera
    if tarea:
        cuerpo += formulario(id_encargo, tarea)
    if estado.get("entrega"):
        cuerpo += f"<div class='tarjeta'><h3 style='margin-top:0'>📦 Propuesta</h3><pre>{html.escape(estado['entrega'])}</pre></div>"
    lineas = "".join(f"<div class='linea'><span class='gris'>{a['cuando'][11:19]}</span> <b>{html.escape(a['quien'])}</b> "
                     f"{html.escape(a['que'])}</div>" for a in estado.get("historial", []))
    tokens = estado.get("tokens", {})
    cuerpo += (f"<div class='tarjeta'><h3 style='margin-top:0'>Qué ha hecho el equipo</h3>{lineas or '…'}"
               f"<p class='gris'>Tokens por agente: {tokens} · total {sum(tokens.values())}</p></div>")
    return pagina(f"{id_encargo} · Faro Digital", cuerpo, refrescar=encargo["estado"] == "trabajando")


if __name__ == "__main__":
    print("📥 Bandeja de tareas en http://127.0.0.1:8000  (Ctrl+C para pararla)")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
