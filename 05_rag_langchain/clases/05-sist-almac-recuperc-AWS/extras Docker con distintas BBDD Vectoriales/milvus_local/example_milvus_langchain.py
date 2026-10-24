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

from langchain_milvus import Milvus

store = Milvus(
    embedding_function=embeddings,
    collection_name="s5_policies_milvus",
    connection_args={"uri": "http://localhost:19530"},
    index_params={"index_type": "AUTOINDEX", "metric_type": "COSINE"},
    consistency_level="Strong",
    auto_id=False,
    drop_old=True,
)
store.add_documents(documents=documents, ids=[f"policy-{position}" for position in range(len(documents))])
for label, expression in (("Sin filtro", None), ("Con filtro", 'country == "ES" and status == "active"')):
    print(label)
    for doc, score in store.similarity_search_with_score(query, k=3, expr=expression):
        print(f"{score:.4f} | {doc.page_content} | {doc.metadata}")
