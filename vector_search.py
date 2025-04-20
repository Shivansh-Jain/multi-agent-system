import json
import os
from typing_extensions import TypedDict
from agents import function_tool
from qdrant_client.models import Filter, models
from qdrant_client import QdrantClient
from fastembed import TextEmbedding


os.makedirs('temp',exist_ok=True)
# Initialize embedding model and Qdrant client
embedding_model = TextEmbedding()
client = QdrantClient(path="temp/qdrant")


class GetContextParams(TypedDict, total=False):
    query: str  # required
    filter: bool  # required
    city: str  # optional


@function_tool
async def get_context(params: GetContextParams) -> str:
    """
    Retrieve relevant documents from Qdrant based on query embedding, optionally filtered by city.

    Args:
        params: Dictionary with 'query', 'filter', and optional 'city' string.

    Returns:
        A JSON string containing a list of matching document payloads.
    """
    query = params["query"]
    apply_filter = params["filter"]
    city = params.get("city")

    embeddings_generator = embedding_model.embed([query])
    embeddings_list = list(embeddings_generator)

    context = []

    if apply_filter and city:
        hits = client.query_points(
            collection_name="my_collection",
            query=embeddings_list[0],
            query_filter=Filter(
                should=[
                    models.FieldCondition(
                        key="city",
                        match=models.MatchValue(value=city),
                    )
                ]
            ),
            limit=5
        )
    else:
        hits = client.query_points(
            collection_name="my_collection",
            query=embeddings_list[0],
            limit=5
        )

    for point in hits.model_dump().get('points', []):
        context.append(point.get('payload', {}))

    # print(context)
    return json.dumps(context)

