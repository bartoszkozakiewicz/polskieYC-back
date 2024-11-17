import sys
import json
sys.path.append(".")
from graph.core import Neo4jService
from graph.schema import ResearchPaper, Scientist
from graph.dao import ResearchPaperDAO, ScientistDAO
from utils_embeddings import Embedder

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
    scdao = ScientistDAO(service, embedder)

    with open(data_path, "r") as f:
        data = json.load(f)

    records: dict[str, list[ResearchPaper]] = dict()
    for _, papers in data.items():
        for paper in papers:
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
    scientists = []
    for record in results:
        assert len(record) == 1
        scientist = record[0]["scientist"]
        papers = record[0]["papers"]
        scientist["summary"] = ""
        for i, paper in enumerate(papers, 1):
            scientist["summary"] += f"\n\n\n# PAPER {i}:\n" + _get_paper_summary(ResearchPaper(**paper))
        scientist = Scientist(**scientist)
        await scdao.add_summary_to_scientist(scientist)
        scientists.append(scientist)

    logger.info("Generating embeddings for scientists")
    tasks = []
    for scientist in scientists:
        tasks.append(scdao.add_embeddings_to_scientist(scientist))
    await asyncio.gather(*tasks)

    await scdao.close()
        
    

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import os
    import sys
    import asyncio

    data_path = "./data/example.json"
    asyncio.run(main(data_path))

    # example