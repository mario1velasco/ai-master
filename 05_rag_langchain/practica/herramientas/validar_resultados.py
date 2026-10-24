"""Paso 8 · Valida resultados.json (12 ejecuciones) sin llamar a ninguna API.

Uso:  ../.venv/bin/python -m herramientas.validar_resultados "Recursos /resultados.json"
Devuelve código 1 si hay ERRORES (estructura o fallos técnicos). Los AVISOS (formato de cita,
abstención probable) son indicios para la revisión manual, no juicios de calidad.
"""
import json
import re
import sys
from pathlib import Path

REGEX_CITA = re.compile(r"\[TENERIFE\.pdf, p\. (\d+)\]")
FRASES_ABSTENCION = ("no contiene", "no incluye", "no menciona", "no aparece", "no indica",
                     "no dispone", "no se especifica", "no hay información", "no puedo")
ESPERADOS = {(f"Q{i}", k) for i in range(1, 7) for k in (2, 4)}


def validar(ruta):
    errores, avisos = [], []
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    claves = [(r["id"], r["k"]) for r in datos]
    if len(datos) != 12:
        errores.append(f"Hay {len(datos)} ejecuciones; deben ser 12.")
    if len(set(claves)) != len(claves):
        errores.append("Hay ejecuciones duplicadas (id, k).")
    faltan = ESPERADOS - set(claves)
    if faltan:
        errores.append(f"Faltan ejecuciones: {sorted(faltan)}")
    for r in datos:
        etiqueta = f"{r['id']} k={r['k']}"
        if r.get("error_tecnico"):
            errores.append(f"{etiqueta}: error técnico ({r['error_tecnico']}). No es una abstención: repite.")
        if not str(r.get("respuesta", "")).strip() and not r.get("error_tecnico"):
            errores.append(f"{etiqueta}: respuesta vacía.")
        if len(r.get("fragmentos", [])) != r["k"] and not r.get("error_tecnico"):
            errores.append(f"{etiqueta}: {len(r.get('fragmentos', []))} fragmentos recuperados y k={r['k']}.")
        citas = REGEX_CITA.findall(r.get("respuesta", ""))
        if r["tipo"] == "respondible":
            if r.get("hit_pagina") not in (0, 1):
                errores.append(f"{etiqueta}: hit_pagina debe ser 0 o 1 en consultas respondibles.")
            if not citas:
                avisos.append(f"{etiqueta}: la respuesta no contiene citas con el formato [TENERIFE.pdf, p. N].")
            elif not r.get("citas_en_paginas_recuperadas"):
                avisos.append(f"{etiqueta}: cita páginas que no están entre las recuperadas.")
        else:
            if r.get("hit_pagina") is not None:
                errores.append(f"{etiqueta}: hit_pagina debe ser None en consultas sin respuesta.")
            if not any(f in r.get("respuesta", "").lower() for f in FRASES_ABSTENCION):
                avisos.append(f"{etiqueta}: no parece una abstención; revisa si inventa el dato.")
    return {"errores": errores, "avisos": avisos, "ejecuciones": len(datos)}


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "Recursos /resultados.json"
    resultado = validar(ruta)
    print(f"{resultado['ejecuciones']} ejecuciones")
    for texto in resultado["errores"]:
        print("ERROR:", texto)
    for texto in resultado["avisos"]:
        print("AVISO:", texto)
    print("OK" if not resultado["errores"] else "Hay errores")
    sys.exit(1 if resultado["errores"] else 0)
