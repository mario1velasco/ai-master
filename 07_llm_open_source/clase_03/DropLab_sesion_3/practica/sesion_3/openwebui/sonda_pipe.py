"""
title: Sonda (qué recibe una Pipe)
description: Devuelve, resumido, lo que Open WebUI entrega a una Pipe. Sirve para comprobar cómo llega una imagen.
"""
# Extensión de la práctica 3 (sesión 3). Instalar a mano: Panel de administración → Funciones → «+».
# Resultado comprobado (Open WebUI 0.12.0, Chromium): la imagen llega en body["messages"][-1]["content"] como
# {"type": "image_url", "image_url": {"url": "data:image/png;base64,…"}}; __files__ llega vacío; y Open WebUI
# añade una parte de texto «<attached_files>…</attached_files>» que NO es la pregunta del usuario.
import json
class Pipe:
    async def pipe(self, body: dict, __files__: list = None, __metadata__: dict = None) -> str:
        def resumir(x):
            if isinstance(x, str) and len(x) > 120: return x[:60] + f"…({len(x)} car.)"
            if isinstance(x, dict): return {k: resumir(v) for k, v in x.items()}
            if isinstance(x, list): return [resumir(v) for v in x]
            return x
        info = {"messages": resumir(body.get("messages")), "files": resumir(__files__),
                "metadata_files": resumir((__metadata__ or {}).get("files")), "claves_body": list(body)}
        return "```json\n" + json.dumps(info, ensure_ascii=False, indent=1)[:6000] + "\n```"
