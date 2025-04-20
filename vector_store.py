from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct,Distance, VectorParams
from typing import List
from fastembed import TextEmbedding
import json

embedding_model = TextEmbedding()
client = QdrantClient(path="temp/qdrant") 


with open('data.json','r') as f:
    data = json.loads(f.read())

docs,payload = [],[]

for city in data:
    for qa in data[city]:
        docs.append(qa['question'])
        payload.append({"city":city,"answer":qa['answer']})

embeddings_generator = embedding_model.embed(docs)
embeddings_list = list(embeddings_generator)


try:
    client.create_collection(
        collection_name="my_collection",
        vectors_config=VectorParams(size=len(embeddings_list[0]), distance=Distance.COSINE),
    )
except:
    pass

client.upsert(
    collection_name="my_collection",
    points=[
        PointStruct(
            id=idx,
            vector=vector.tolist(),
            payload=payload[idx]
        )
        for idx, vector in enumerate(embeddings_list)
    ]
)