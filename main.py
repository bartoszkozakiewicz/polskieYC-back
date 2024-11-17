from enum import Enum
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph.dao import ScientistDAO
from graph.core import Neo4jService
from utils_embeddings import Embedder

from dotenv import load_dotenv
load_dotenv()

class UserType(str, Enum):
    investors = "investors"
    academia = "academia"
    business = "business"


class SearchRequest(BaseModel):
    user_type: UserType
    query: str
    n_results: int = Field(10, ge=1, le=100)


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "root"}


@app.get("/test")
async def test():
    return {"message": "Hello World"}


@app.post("/search")
async def search(request: SearchRequest):
    responses = {
        UserType.investors: "investors",
        UserType.academia: "academia",
        UserType.business: "business",
    }
    
    user_message = responses.get(request.user_type)
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    # Placeholder for actual search logic
    if user_message == "academia":
        service = Neo4jService(
            os.getenv("NEO4J_URI"),
            os.getenv("NEO4J_USER"),
            os.getenv("NEO4J_PASSWORD"),
            "neo4j"
        )
        embedder = Embedder()
        scdao = ScientistDAO(service, embedder) 
        search_results = await scdao.search_scientists_by_query(request.query, request.n_results)
        return {"user_type": user_message, "query": request.query, "results": search_results}


    return {"user_type": user_message, "query": request.query, "results": search_results}
