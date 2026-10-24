# Validación — 16 de septiembre de 2026

- Notebook validado como JSON y mediante el esquema nbformat 4.5.
- 28 celdas: 13 Markdown y 15 de código; código analizado y ejecutado en orden con Python 3.12 en macOS.
- Ejecución completa comprobada sin ambas claves, sin OPENAI_API_KEY y sin PINECONE_API_KEY: sin conexiones remotas ni errores que interrumpan las demás celdas.
- Corpus determinista: 128 documentos, 128 IDs únicos y ocho registros elegibles para España/personal interno/vigente.
- Imports y firmas revisados con las integraciones instaladas. Los tres scripts adicionales compilan y terminan con un mensaje útil si falta la clave de OpenAI.
- Dependencias principales y adicionales instaladas conjuntamente en un entorno aislado; comprobación de dependencias sin conflictos.
- Los tres Compose se validaron como YAML. Milvus utiliza el archivo oficial v3.0.1, con puertos limitados a loopback y sin el campo obsoleto version.
- Comprobación del notebook para excluir referencias pedagógicas y comprobar que no depende de Docker.

**Límites de verificación:** no se realizaron llamadas a OpenAI/Pinecone con credenciales reales, ni se arrancaron los contenedores. CRUD remoto, rankings, latencias, acceso a la región y salud de los despliegues requieren ejecutar los archivos con servicios disponibles. La guía es multiplataforma; la ejecución local de validación se realizó en macOS.

## Versiones fijadas

Las dependencias directas se fijan en sus respectivos requirements. El SDK Pinecone se fija en 7.3.0 porque langchain-pinecone 0.2.13 declara `pinecone[asyncio]>=6.0.0,<8.0.0`; no se fuerza SDK 10.0.0, que es incompatible con ese rango. Python 3.12 evita el límite `<3.14` de esa integración.

Fuentes de dependencias: [langchain-pinecone 0.2.13](https://pypi.org/project/langchain-pinecone/0.2.13/), [SDK Pinecone 7.3.0](https://pypi.org/project/pinecone/7.3.0/).

| Servicio adicional | Imagen |
|---|---|
| Qdrant | qdrant/qdrant:v1.19.1 |
| Milvus | milvusdb/milvus:v3.0.1 |
| Weaviate | cr.weaviate.io/semitechnologies/weaviate:1.39.5 |

Referencias de despliegue: [Qdrant v1.19.1](https://github.com/qdrant/qdrant/releases/tag/v1.19.1), [Compose Milvus](https://milvus.io/docs/install_standalone-docker-compose.md), [Docker Weaviate](https://docs.weaviate.io/deploy/installation-guides/docker-installation).
