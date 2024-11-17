import json
import os
import sys
sys.path.append(".")
from graph.schema import Problem
from graph.core import Neo4jService
from graph.dao import ProblemDAO
from utils_llms import Embedder

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _do_tasks_with_func(func, task_args_list=None, task_kwargs_list=None):
    if not task_args_list and not task_kwargs_list:
        raise ValueError("Either task_args or task_kwargs_list must be provided")
    elif not task_args_list:
        task_args_list = [tuple()] * len(task_kwargs_list)
    elif not task_kwargs_list:
        task_kwargs_list = [{}] * len(task_args_list)
    
    if not isinstance(task_args_list, list):
        task_args_list = [task_args_list]

    if not isinstance(task_kwargs_list, list):
        task_kwargs_list = [task_kwargs_list]

    tasks = []
    for args, kwargs in zip(task_args_list, task_kwargs_list):
        if not isinstance(args, tuple):
            args = (args,)
        tasks.append(func(*args, **kwargs))
    return asyncio.gather(*tasks)


async def main(business_problems_path):
    with open(business_problems_path) as f:
        business_problems = json.load(f)
    problems = [Problem(**p) for p in business_problems]

    service = Neo4jService(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
        "neo4j"
    )

    embedder = Embedder()
    scdao = ProblemDAO(service, embedder)
    logger.info("Adding problems to the graph")
    _do_tasks_with_func(scdao.add_problem, problems)

    logger.info("Fetching problems from the graph")
    business_problems = await scdao.get_all_problems_without_embeddings()
    print(len(business_problems))
    
    logger.info("Adding embeddings to the problem nodes")
    # _do_tasks_with_func(scdao.add_embeddings_to_problem, business_problems)
    # tasks = []
    for problem in business_problems:
        await scdao.add_embeddings_to_problem(problem)
        # tasks.append(task)
    # asyncio.gather(*tasks)

    await scdao.close()

    return business_problems

if __name__ == "__main__":
    import asyncio
    import sys
    from dotenv import load_dotenv
    load_dotenv()
    business_problems_path = "data/trending_problems.json"
    asyncio.run(main(business_problems_path))