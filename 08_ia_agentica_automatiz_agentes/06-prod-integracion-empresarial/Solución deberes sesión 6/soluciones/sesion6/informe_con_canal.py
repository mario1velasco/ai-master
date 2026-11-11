"""Solución · Deber guiado de la sesión 6: el informe diario, programado y publicado en un canal.

La URL del webhook entrante se lee de la variable INFORME_WEBHOOK_URL del archivo
.env, para no dejarla escrita en el comando ni en la tarea programada (cualquiera
con esa URL puede publicar en el canal). Si no está definida, el informe solo se
guarda en datos/informes/.

Uso:  python -m soluciones.sesion6.informe_con_canal
Programación: ver PROGRAMAR.md en esta misma carpeta.
"""
import os

from comun.llm import load_dotenv  # noqa: F401  (carga el .env al importar comun.llm)
from sesion6.informe_programado import SERVIDOR, generar_informe, publicar


def ejecutar(modelo=None, servidor: str = None, http=None, carpeta=None) -> dict:
    opciones = {k: v for k, v in {"modelo": modelo, "servidor": servidor or os.getenv("TICKETS_URL", SERVIDOR),
                                  "http": http, "carpeta": carpeta}.items() if v is not None}
    ruta = generar_informe(**opciones)
    url = os.getenv("INFORME_WEBHOOK_URL", "").strip()
    if not url:
        return {"informe": ruta, "publicado": False}
    respuesta = publicar(ruta, url, http=http) if http else publicar(ruta, url)
    return {"informe": ruta, "publicado": respuesta.status_code == 200}


if __name__ == "__main__":
    resultado = ejecutar()
    print(f"📄 {resultado['informe']} · {'publicado en el canal' if resultado['publicado'] else 'no publicado (sin INFORME_WEBHOOK_URL)'}")
