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
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore

client = QdrantClient(url="http://localhost:6333")
collection_name = "s5_policies_qdrant"
try:
    if not client.collection_exists(collection_name):
        client.create_collection(collection_name, vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE))
    store = QdrantVectorStore(client=client, collection_name=collection_name, embedding=embeddings)
    ids = [str(uuid5(NAMESPACE_URL, f"s5-qdrant-policy-{position}")) for position in range(len(documents))]
    store.add_documents(documents=documents, ids=ids)
    metadata_filter = models.Filter(must=[
        models.FieldCondition(key="metadata.country", match=models.MatchValue(value="ES")),
        models.FieldCondition(key="metadata.status", match=models.MatchValue(value="active")),
    ])
    for label, expression in (("Sin filtro", None), ("Con filtro", metadata_filter)):
        print(label)
        for doc, score in store.similarity_search_with_score(query, k=3, filter=expression):
            print(f"{score:.4f} | {doc.page_content} | {doc.metadata}")
finally:
    client.close()
