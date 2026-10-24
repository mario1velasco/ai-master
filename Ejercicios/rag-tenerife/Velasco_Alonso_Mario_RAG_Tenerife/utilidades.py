"""Infraestructura suministrada. No contiene las soluciones de los TODO."""
from pathlib import Path
import csv
import json
import re
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser


def cargar_paginas(ruta):
    """Extrae texto sin renumerar páginas ni interpretar imágenes/enlaces."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"Coloca la guía original en {ruta}")
    reader = PdfReader(ruta)
    documentos, vacias = [], []
    for numero, pagina in enumerate(reader.pages, start=1):
        texto = (pagina.extract_text() or "").strip()
        if not texto:
            vacias.append(numero)
            continue
        documentos.append(Document(page_content=texto, metadata={
            "source": ruta.name, "page": numero}))
    if not documentos:
        raise ValueError("No se ha extraído texto. Revisa el PDF.")
    return documentos, {"paginas_pdf": len(reader.pages),
                        "paginas_con_texto": len(documentos),
                        "paginas_sin_texto": vacias}


def leer_preguntas(ruta="preguntas.csv"):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    for fila in filas:
        fila["paginas_referencia"] = [int(p) for p in
            fila["paginas_referencia"].split(";") if p.strip()]
    return filas


def construir_contexto(documentos):
    return "\n\n".join(
        f"[{d.metadata['source']}, p. {d.metadata['page']}] "
        f"(fragmento {d.metadata['chunk_id']})\n{d.page_content}"
        for d in documentos)


def ejecutar_pruebas(indice, modelo, prompt, preguntas, recuperar, hit_pagina,
                     salida=Path(".")):
    """Solo la pregunta llega al buscador; la referencia se usa después."""
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    cadena = prompt | modelo | StrOutputParser()
    registros = []
    for k in (2, 4):
        for caso in preguntas:
            docs = []
            respuesta = ""
            error = ""
            try:
                docs = recuperar(indice, caso["pregunta"], k)
                # ! Pondriamos un reranking aquí si queremos, pero no es obligatorio. Consulta + fragmentos
                # ! Pondriamos un reranking aquí si queremos, pero no es obligatorio. Consulta + fragmentos
                # ! Pondriamos un reranking aquí si queremos, pero no es obligatorio. Consulta + fragmentos
                respuesta = cadena.invoke({"pregunta": caso["pregunta"],
                                           "contexto": construir_contexto(docs)})
            except Exception as exc:
                # No volcar mensajes del proveedor que puedan incluir credenciales.
                error = type(exc).__name__
            paginas = [d.metadata["page"] for d in docs]
            citadas = [int(x) for x in re.findall(
                r"\[TENERIFE\.pdf, p\. (\d+)\]", respuesta)]
            registros.append({
                "id": caso["id"], "tipo": caso["tipo"], "k": k,
                "pregunta": caso["pregunta"], "respuesta": respuesta,
                "error_tecnico": error,
                "fragmentos": [{"id": d.metadata["chunk_id"],
                    "source": d.metadata["source"], "page": d.metadata["page"],
                    "texto": d.page_content} for d in docs],
                "hit_pagina": hit_pagina(paginas, caso["paginas_referencia"]),
                "paginas_citadas": citadas,
                # Este chequeo NO valida el respaldo semántico de las citas.
                "citas_en_paginas_recuperadas": bool(citadas) and
                    set(citadas).issubset(set(paginas)),
            })
            # Guardar progresivamente para no perder pruebas si se interrumpe.
            (salida / "resultados.json").write_text(
                json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")
    revision = salida / "revision.csv"
    if not revision.exists():
        campos = ["id", "k", "tipo", "hit_pagina", "respaldo", "citas",
                  "abstencion", "observaciones"]
        with revision.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for r in registros:
                writer.writerow({"id": r["id"], "k": r["k"], "tipo": r["tipo"],
                    "hit_pagina": "NA" if r["hit_pagina"] is None else r["hit_pagina"],
                    "respaldo": "" if r["tipo"] == "respondible" else "NA",
                    "citas": "" if r["tipo"] == "respondible" else "NA",
                    "abstencion": "NA" if r["tipo"] == "respondible" else "",
                    "observaciones": r["error_tecnico"]})
    else:
        print("revision.csv ya existe y se conserva. Si cambiaste resultados, "
              "guarda copia y vuelve a revisar las 12 filas.")
    return registros


def resumen_revision(ruta="revision.csv"):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    if len(filas) != 12 or len({(r["id"], r["k"]) for r in filas}) != 12:
        raise ValueError("La revisión debe tener 12 filas distintas.")
    for k in ("2", "4"):
        grupo = [r for r in filas if r["k"] == k]
        print(f"k = {k}")
        for campo, tipo, n in [("hit_pagina", "respondible", 4),
                                ("respaldo", "respondible", 4),
                                ("citas", "respondible", 4),
                                ("abstencion", "sin_respuesta", 2)]:
            valores = [r[campo] for r in grupo if r["tipo"] == tipo]
            if len(valores) != n or any(v not in ("0", "1") for v in valores):
                print(f"  {campo}: pendiente de revisar ({n} casos)")
            else:
                total = sum(map(int, valores))
                print(f"  {campo}: {total}/{n} = {total/n:.2f}")
