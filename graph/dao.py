import json
from core import Neo4jService
from schema import BaseSchema, ResearchPaper, Scientist, Problem

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
    def __init__(self, service: Neo4jService):
        super().__init__(service)

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


def _get_paper_summary(paper: ResearchPaper):
    return (
        "## TITLE:\n",
        paper.title,

        "\n\n## ABSTRACT:\n",
        paper.abstract,

        "\n\n## PUBLISHED DATE:\n",
        paper.published_date
    )

async def main(data_path: str):
    service = Neo4jService(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
        "neo4j"
    )

    rpdao = ResearchPaperDAO(service)
    scdao = ScientistDAO(service)

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
                        abstract=paper["abstract"]
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
    for record in results:
        assert len(record) == 1
        scientist = record[0]["scientist"]
        papers = record[0]["papers"]
        scientist["summary"] = ""
        for i, paper in enumerate(papers, 1):
            scientist["summary"] += f"\n\n\n# PAPER {i}:\n" + _get_paper_summary(ResearchPaper(**paper))
        await scdao.add_summary_to_scientist(Scientist(**scientist))


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
        