import arxiv
from unidecode import unidecode
import json
from tqdm import tqdm


def fetch_arxiv_papers(query, max_results=100):

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    for result in arxiv.Client().results(search):
        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "published_date": result.published.strftime("%Y-%m-%d"),
            "link": result.entry_id,
            "abstract": result.summary,
        }
        papers.append(paper)
    
    return papers


def get_authors():
    authors = []
    with open("./phds.txt", "r") as f:
        for line in f:
            authors.append(line.strip())
    return authors


def prepare_author_query(author):
    name, surname = author.split(" ", 1)
    surname = "_".join(surname.split())
    return f"au:{unidecode(surname).lower()}_{unidecode(name).lower()}"


def prepare_rg_suffix(author):
    name, surname = author.split(" ", 1)
    surname = "-".join(surname.split())
    return f"{unidecode(name)}-{unidecode(surname)}"


if __name__ == "__main__":
    authors = get_authors()

    # title, authors, published_date, link, abstract

    result = {}

    for author in tqdm(authors):
        query = prepare_author_query(author)
        papers = fetch_arxiv_papers(query, max_results=20)
        rg_suffix = prepare_rg_suffix(author)
        result[author] = {"researchgate": f"https://www.researchgate.net/profile/{rg_suffix}", "papers": papers}


    with open("papers.json", "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)
    

