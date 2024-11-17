from typing import Optional
from enum import Enum
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from graph.dao import ScientistDAO, ProblemDAO
from graph.core import Neo4jService
from utils_embeddings import Embedder

from dotenv import load_dotenv
load_dotenv()

class UserType(str, Enum):
    projects = "Projects"
    researchers = "Researchers"
    business = "Businesses"


class SearchRequest(BaseModel):
    user_type: str
    query: str
    n_results: Optional[int] = Field(10, ge=1, le=100)


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
        UserType.projects: "projects",
        UserType.researchers: "researchers",
        UserType.business: "business",
    }
    
    user_message = responses.get(request.user_type)
    
    if not user_message:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    service = Neo4jService(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
        "neo4j"
    )
    embedder = Embedder()
    if user_message == "researchers":
        scdao = ScientistDAO(service, embedder) 
        search_results = await scdao.search_scientists_by_query(request.query, request.n_results)
        to_ret = {"user_type": user_message, "query": request.query, "results": search_results}
    elif user_message == "projects":
        pdao = ProblemDAO(service, embedder)
        search_results = await pdao.search_problems_by_query(request.query, request.n_results)
        to_ret = {"user_type": user_message, "query": request.query, "results": search_results}
    else:
        to_ret = {"user_type": user_message, "query": request.query, "results": []}
    print(to_ret)
    return to_ret


    return {"user_type": user_message, "query": request.query, "results": search_results}
