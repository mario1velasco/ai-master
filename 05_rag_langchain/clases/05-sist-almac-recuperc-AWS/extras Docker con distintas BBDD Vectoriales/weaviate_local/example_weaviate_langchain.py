import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

load_dotenv(Path(__file__).with_name(".env"))
if not os.getenv("OPENAI_API_KEY", "").strip():
    raise SystemExit("Configura OPENAI_API_KEY en el .env de esta carpeta.")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1536)
documents = [
    Document(page_content="España: el personal interno solicita vacaciones en el portal de personas con aprobación del responsable.", metadata={"country": "ES", "status": "active", "employee_type": "internal"}),
    Document(page_content="México: el personal interno solicita vacaciones mediante la oficina de personas local.", metadata={"country": "MX", "status": "active", "employee_type": "internal"}),
    Document(page_content="España: el procedimiento antiguo de vacaciones utilizaba un formulario por correo.", metadata={"country": "ES", "status": "archived", "employee_type": "internal"}),
]
query = "¿Cómo solicito vacaciones?"

from uuid import uuid5, NAMESPACE_URL
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from langchain_weaviate import WeaviateVectorStore

if not os.getenv("WEAVIATE_API_KEY", "").strip():
    raise SystemExit("Configura WEAVIATE_API_KEY en el .env de esta carpeta y reinicia Docker Compose.")

client = weaviate.connect_to_local(auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]))
try:
    collection_name = "S5PoliciesWeaviate"
    # Solo se recrea la colección dedicada al ejemplo.
    if client.collections.exists(collection_name):
        client.collections.delete(collection_name)
    store = WeaviateVectorStore(client=client, index_name=collection_name,
                               text_key="text", embedding=embeddings,
                               attributes=["country", "status", "employee_type"])
    ids = [str(uuid5(NAMESPACE_URL, f"s5-weaviate-policy-{position}")) for position in range(len(documents))]
    store.add_documents(documents=documents, ids=ids)
    metadata_filter = Filter.by_property("country").equal("ES") & Filter.by_property("status").equal("active")
    for label, expression in (("Sin filtro", None), ("Con filtro", metadata_filter)):
        print(label)
        for doc in store.similarity_search(query, k=3, filters=expression, alpha=1.0):
            print(f"{doc.page_content} | {doc.metadata}")
finally:
    client.close()
