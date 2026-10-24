from __future__ import annotations

import os
from langchain_core.embeddings import Embeddings


class GeminiEmbeddings(Embeddings):
    """Embedding 2: instrucciones textuales y un Content por documento."""

    def __init__(self, model="gemini-embedding-2", dimension=3072):
        from google import genai
        from google.genai import types

        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                                   http_options=types.HttpOptions(timeout=120000,
                                       retry_options=types.HttpRetryOptions(attempts=1)))
        self.model, self.dimension = model, dimension

    def _encode(self, texts):
        from google.genai import types

        contents = [types.Content(parts=[types.Part.from_text(text=t)]) for t in texts]
        result = self.client.models.embed_content(
            model=self.model, contents=contents,
            config=types.EmbedContentConfig(output_dimensionality=self.dimension))
        values = [embedding.values for embedding in result.embeddings]
        if len(values) != len(texts):
            raise ValueError("Gemini no devolvió un embedding independiente por entrada.")
        return values

    def embed_documents(self, texts):
        inputs = []
        for text in texts:
            title, separator, body = text.partition("\n\n")
            inputs.append(f"title: {title} | text: {body}" if separator else f"title: none | text: {text}")
        return self._encode(inputs)

    def embed_query(self, text):
        return self.embed_queries([text])[0]

    def embed_queries(self, texts):
        return self._encode([f"task: search result | query: {text}" for text in texts])


def build_embedder(spec):
    if spec.provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=spec.name, dimensions=spec.native_dimension,
                                chunk_size=100, max_retries=0, request_timeout=120,
                                check_embedding_ctx_length=False)
    if spec.provider == "gemini":
        return GeminiEmbeddings(spec.name, spec.native_dimension)
    if spec.provider == "huggingface":
        import torch
        from langchain_huggingface import HuggingFaceEmbeddings

        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        prompt = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "
        print(f"Qwen: dispositivo {device}. La primera carga puede descargar los pesos.")
        return HuggingFaceEmbeddings(
            model_name=spec.name, model_kwargs={"device": device, "revision": spec.revision},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 8, "prompt": ""},
            query_encode_kwargs={"normalize_embeddings": True, "prompt": prompt})
    raise ValueError(f"Proveedor no implementado: {spec.provider}")
