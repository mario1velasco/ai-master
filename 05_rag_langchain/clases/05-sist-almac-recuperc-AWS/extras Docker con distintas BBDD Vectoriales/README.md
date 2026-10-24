# Material adicional

Estos tutoriales son opcionales para realizar fuera de la sesión. Cada carpeta es autocontenida y tiene su propio entorno y despliegue. No forman parte del flujo del notebook principal.

- `qdrant_local/`: Qdrant con Docker Compose y filtros de payload.
- `milvus_local/`: Milvus standalone con etcd y MinIO, mediante Compose oficial.
- `weaviate_local/`: Weaviate con autenticación por clave y embeddings externos.

Los scripts utilizan LangChain y OpenAIEmbeddings. El almacenamiento es local; los embeddings se envían a OpenAI. Ejecuta un tutorial cada vez para simplificar recursos y puertos.
