import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

index_name = os.environ.get("PINECONE_INDEX", "casestudy-index")
if index_name not in [idx.name for idx in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=1536,      
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  
    )

index = pc.Index(index_name)

def upsert_case(case_id: str, vector: list[float], metadata: dict | None = None):
    index.upsert(vectors=[{"id": case_id, "values": vector, "metadata": metadata or {}}])

def query_similar(vec: list[float], top_k=5):
    return index.query(vector=vec, top_k=top_k, include_values=False, include_metadata=True)


