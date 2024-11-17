import os

from .core import Neo4jService
from .schema import BaseSchema, ResearchPaper, Scientist, Problem
import cohere
import sys
sys.path.append(".")
from utils_llms import Embedder

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseDAO:
    def __init__(self, service: Neo4jService):
        self.service = service
        if not self.service.driver:
            self.service.open()

    async def close(self):
        await self.service.close()


def _model_to_neo4j_args(model: BaseSchema):
    model_dict = model.to_dict()
    return "{" + ", ".join(f"{key}: ${key}" for key, val in model_dict.items() if val is not None) + "}"


class ResearchPaperDAO(BaseDAO):
    def __init__(self, service: Neo4jService):
        super().__init__(service)

    def _add_research_paper(self, tx, paper: ResearchPaper):
        model_args = _model_to_neo4j_args(paper)
        query = (
            f"MERGE (paper:ResearchPaper {model_args}) "
            "RETURN paper"
        )
        return tx.run(query, **paper.to_dict())
    
    def _add_research_paper_to_scientist(self, tx, scientist_email: str, paper_title: str):
        query = (
            "MATCH (scientist:Scientist {email: $scientist_email}) "
            "MATCH (paper:ResearchPaper {title: $paper_title}) "
            "MERGE (scientist)-[:AUTHORED]->(paper) "
            "RETURN scientist, paper"
        )
        return tx.run(query, scientist_email=scientist_email, paper_title=paper_title)
    
    async def add_research_paper(self, paper: ResearchPaper):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_research_paper, paper)
        
    async def add_research_paper_to_scientist(self, scientist: Scientist, paper: ResearchPaper):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_research_paper_to_scientist, scientist.email, paper.title)
        
    async def add_all_papers_from_scientist(self, scientist: Scientist, papers: list[ResearchPaper]):
        async with self.service.driver.session() as session:
            for paper in papers:
                await session.execute_write(self._add_research_paper, paper)
                await session.execute_write(self._add_research_paper_to_scientist, scientist.email, paper.title)


class ScientistDAO(BaseDAO):
    def __init__(self, service: Neo4jService, embedder: Embedder):
        super().__init__(service)
        self.embedder = embedder

    def _add_scientist(self, tx, scientist: Scientist):
        model_args = _model_to_neo4j_args(scientist)
        query = (
            f"MERGE (scientist:Scientist {model_args}) "
            "RETURN scientist"
        )
        return tx.run(query, **scientist.to_dict())
    
    async def add_scientist(self, scientist: Scientist):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_scientist, scientist)
    
    async def _get_scientist_and_papers_by_scientist_name(self, tx, name: str):
        query = (
            "MATCH (scientist:Scientist {name: $name})-[:AUTHORED]->(paper:ResearchPaper) "
            "RETURN scientist, collect(paper) as papers"
        )
        result = await tx.run(query, name=name)
        return await result.data()
    
    async def get_scientist_and_papers_by_scientist_name(self, name: str):
        async with self.service.driver.session() as session:
            results = await session.execute_read(self._get_scientist_and_papers_by_scientist_name, name=name)
            return results
                
    def _add_summary_to_scientist(self, tx, scientist: Scientist):
        new_scientist = scientist.model_copy()
        new_scientist.summary = None
        model_args = _model_to_neo4j_args(new_scientist)
        query = (
            f"MATCH (scientist:Scientist {model_args}) "
            "SET scientist.summary = $summary "
            "RETURN scientist"
        )
        return tx.run(query, **scientist.to_dict())
    
    async def add_summary_to_scientist(self, scientist: Scientist):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_summary_to_scientist, scientist)
        
    async def _add_embeddings_to_scientist(self, tx, scientist: Scientist):
        model_args = _model_to_neo4j_args(scientist)

        embedding = await self.embedder.get_embeddings(scientist.summary)
        embedding = embedding[0]
        kwargs = {key: val for key, val in scientist.to_dict().items() if val is not None}

        query = (
            f"MATCH (scientist:Scientist {model_args}) "
            "SET scientist.embedding = $embedding "
            "RETURN scientist"
        )
        return await tx.run(query, **kwargs, embedding=embedding)
    
    async def add_embeddings_to_scientist(self, scientist: Scientist):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_embeddings_to_scientist, scientist)
        

    async def _search_scientists_by_query(self, tx, query: str, n_results: int = 10):
        embedded_question = await self.embedder.get_embeddings(query)
        embedded_question = embedded_question[0]

        query = (
            "CALL db.index.vector.queryNodes('ScientistIndex', $limit, $embedded_question) YIELD node as scientist, score "
            "RETURN scientist "
        )

        result = await tx.run(query, embedded_question=embedded_question, limit=n_results*2)
        result = await result.data()
        result = [{key: val for key, val in record["scientist"].items() if key != "embedding"} for record in result]

        api_key = os.getenv("COHERE_API_KEY")
        co = cohere.ClientV2(api_key=api_key)

        results_for_reranker = [{"text": d["summary"]} for d in result]
        ordering = co.rerank(query=query,
                    documents=results_for_reranker,
                    top_n=n_results,
                    model='rerank-english-v3.0').results
        ordering = [o.index for o in ordering]
        result = [result[i] for i in ordering]
        
        return result
    
    async def search_scientists_by_query(self, query: str, n_results: int = 10):
        async with self.service.driver.session() as session:
            results = await session.execute_read(self._search_scientists_by_query, query, n_results)
            return results
        

class ProblemDAO(BaseDAO):
    def __init__(self, service: Neo4jService, embedder: Embedder):
        super().__init__(service)
        self.embedder = embedder

    def _add_problem(self, tx, problem: Problem):
        model_args = _model_to_neo4j_args(problem)
        query = (
            f"MERGE (problem:Problem {model_args}) "
            "RETURN problem"
        )
        return tx.run(query, **problem.to_dict())
    
    async def add_problem(self, problem: Problem):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_problem, problem)
        
    async def _get_all_problems_without_embeddings(self, tx):
        query = (
            "MATCH (p:Problem) WHERE p.embedding IS NULL RETURN p "
        )
        result = await tx.run(query)
        return await result.data()
    
    async def get_all_problems_without_embeddings(self):
        async with self.service.driver.session() as session:
            results = await session.execute_read(self._get_all_problems_without_embeddings)
            results = [Problem(**record["p"]) for record in results]
            return results
        

    async def _add_embeddings_to_problem(self, tx, problem: Problem):
        model_args = _model_to_neo4j_args(problem)

        embedding = await self.embedder.get_embeddings(problem.description)
        embedding = embedding[0]
        kwargs = {key: val for key, val in problem.to_dict().items() if val is not None}

        query = (
            f"MATCH (problem:Problem {model_args}) "
            "SET problem.embedding = $embedding "
            "RETURN problem"
        )
        return await tx.run(query, **kwargs, embedding=embedding)
    
    async def add_embeddings_to_problem(self, problem: Problem):
        async with self.service.driver.session() as session:
            return await session.execute_write(self._add_embeddings_to_problem, problem)
        
    async def _search_problems_by_query(self, tx, query: str, n_results: int = 10, index='ProblemIndex'):
        embedded_question = await self.embedder.get_embeddings(query)
        embedded_question = embedded_question[0]

        query = (
            f"CALL db.index.vector.queryNodes('{index}', $limit, $embedded_question) YIELD node as problem, score "
            "RETURN problem"
        )
        result = await tx.run(query, embedded_question=embedded_question, limit=n_results)
        result = await result.data()
        result = [{key: val for key, val in record["problem"].items() if key != "embedding"} for record in result]

        api_key = os.getenv("COHERE_API_KEY")
        co = cohere.ClientV2(api_key=api_key)

        results_for_reranker = [{"text": d["description"]} for d in result]
        ordering = co.rerank(query=query,
                    documents=results_for_reranker,
                    top_n=n_results,
                    model='rerank-english-v3.0').results
        ordering = [o.index for o in ordering]
        result = [result[i] for i in ordering]

        return result
    
    async def search_problems_by_query(self, query: str, n_results: int = 10, index='ProblemIndex'):
        async with self.service.driver.session() as session:
            results = await session.execute_read(self._search_problems_by_query, query, n_results, index)
            return results
        

        