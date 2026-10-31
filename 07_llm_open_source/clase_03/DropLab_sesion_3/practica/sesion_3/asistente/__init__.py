"""El Asistente DropLab (sesión 3): visión, datos y documentos detrás de una API.

Módulos reutilizables (la lógica vive aquí; los scripts 00–09 y la API solo los llaman):

    config       rutas, URLs y modelos (se pueden cambiar con variables de entorno)
    ollama       cliente de Ollama con tiempos medidos y errores identificables
    vision       esquemas Pydantic, extracción con un VLM y comparación con los registros
    datos        consultas de solo lectura y con parámetros sobre la capa semántica (sesión 2)
    documentos   el RAG de la sesión 2 (12_buscar.py y 13_preguntar_documentos.py), con el índice ampliado (junio)
    lectura      documentos difíciles: limpiar la lectura de PaddleOCR-VL, comprobar cifras y poner la ficha
    flujo        el flujo con LangGraph: planificar → ticket / cifras / documentos → contrastar → redactar
    flujo_simple el mismo proceso con funciones de Python, sin framework
    api          la API con FastAPI (OpenAPI en /docs)
"""
