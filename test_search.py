from graph.core import Neo4jService
from graph.dao import ResearchPaperDAO, ScientistDAO
from utils_llms import Embedder


async def test_search(data_path: str):
    import os
    import asyncio

    service = Neo4jService(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
        "neo4j"
    )

    # rpdao = ResearchPaperDAO(service)
    embedder = Embedder()
    scdao = ScientistDAO(service, embedder)

    query = "Manufacturing predictive maintenance"
    results = await scdao.search_scientists_by_query(query)
    print(results)

    await scdao.close()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import os
    import sys
    import asyncio

    data_path = "./data/example.json"
    asyncio.run(test_search(data_path))
    