import sys
import json
from typing import Any
sys.path.append(".")

from openai import AsyncOpenAI

from graph.core import Neo4jService
from graph.schema import ResearchPaper, Scientist
from graph.dao import ResearchPaperDAO, ScientistDAO
from utils_llms import Embedder, Describer

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_paper_summary(paper: ResearchPaper):
    return (
        "## TITLE:\n"
        f"{paper.title}"

        "\n\n## ABSTRACT:\n"
        f"{paper.abstract}"

        "\n\n## PUBLISHED DATE:\n"
        f"{paper.published_date}"
    )

async def main(data_path: str):
    service = Neo4jService(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
        "neo4j"
    )

    rpdao = ResearchPaperDAO(service)
    embedder = Embedder()
    describer = Describer()
    scdao = ScientistDAO(service, embedder)

    with open(data_path, "r") as f:
        data = json.load(f)

    records: dict[str, dict[str, Any]] = dict()
    for person, values in data.items():
        researchgate_url = values["researchgate"]
        for paper in values["papers"]:
            for author in paper["authors"]:
                if author not in records:
                    records[author] = []
                records[author].append(
                    ResearchPaper(
                        title=paper["title"],
                        abstract=paper["abstract"],
                        published_date=paper["published_date"],
                        url=paper["link"],
                    )
                )

    logger.info("Adding scientists to the database")
    tasks = []
    for scientist_name in records.keys():
        scientist = Scientist(
            name=scientist_name,
            email=f"{scientist_name.replace(' ', '')}@pw.edu.pl",
            affiliation="Warsaw University of Technology"
        )
        task = scdao.add_scientist(scientist)
        tasks.append(task)
    await asyncio.gather(*tasks)

    logger.info("Adding papers to the database")
    tasks = []
    for scientist_name, papers in records.items():
        scientist = Scientist(
            name=scientist_name,
            email=f"{scientist_name.replace(' ', '')}@pw.edu.pl",
            affiliation="Warsaw University of Technology"
        )
        await rpdao.add_all_papers_from_scientist(scientist, papers)

    logger.info("Fetching all papers by scientist")
    tasks = []
    for scientist_name in records.keys():
        task = scdao.get_scientist_and_papers_by_scientist_name(scientist_name)
        tasks.append(task)
    results = await asyncio.gather(*tasks)

    logger.info("Generating description of the scientists")
    tasks = []
    scientists = []
    for record in results:
        assert len(record) == 1
        scientist = record[0]["scientist"]
        papers = record[0]["papers"]
        summary = ""
        for i, paper in enumerate(papers, 1):
            summary += f"\n\n\n# PAPER {i}:\n" + _get_paper_summary(ResearchPaper(**paper))

        tasks.append(describer.get_descriptions([summary]))
        scientists.append(scientist)

    descriptions = await asyncio.gather(*tasks)

    new_scientists = []
    for scientist, description in zip(scientists, descriptions):
        scientist["summary"] = description[0] if isinstance(description, list) else description
        scientist = Scientist(**scientist)
        await scdao.add_summary_to_scientist(scientist)
        new_scientists.append(scientist)

    logger.info("Generating embeddings for scientists")
    tasks = []
    for scientist in new_scientists:
        scientist.embedding = None
        tasks.append(scdao.add_embeddings_to_scientist(scientist))
    await asyncio.gather(*tasks)

    await scdao.close()
        
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import os
    import sys
    import asyncio

    data_path = "./data/papers_long.json"
    asyncio.run(main(data_path))

    # example