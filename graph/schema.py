from typing import Optional
from pydantic import BaseModel, Field

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

    def to_dict(self):
        return self.__dict__
    

class ResearchPaper(BaseSchema):
    title: str = Field(..., title="Title of the research paper")
    abstract: str = Field(..., title="Abstract of the research paper")
    summary: Optional[str] = Field(None, title="Summary of the research paper")
    tags: Optional[list[str]] = Field(None, title="Tags of the research paper")


class Scientist(BaseSchema):
    name: str = Field(..., title="Name of the scientist")
    email: str = Field(..., title="Email of the scientist")
    research_papers: Optional[list[ResearchPaper]] = Field(None, title="Research papers of the scientist")
    summary: Optional[str] = Field(None, title="Summary of the scientist")
    tags: Optional[list[str]] = Field(None, title="Tags of the scientist")
    embedding: Optional[list[float]] = Field(None, title="Embedding of the scientist")


class Problem(BaseSchema):
    description: str = Field(..., title="Description of the problem")
    tags: Optional[list[str]] = Field(None, title="Tags of the problem")
    embedding: Optional[list[float]] = Field(None, title="Embedding of the problem")


# class Company(BaseSchema):
#     name: str = Field(..., title="Name of the company")
#     description: str = Field(..., title="Description of the company")
#     tags: Optional[list[str]] = Field(None, title="Tags of the company")
#     embedding: Optional[list[float]] = Field(None, title="Embedding of the company")


# class VC(BaseSchema):
#     name: str = Field(..., title="Name of the VC")
#     description: str = Field(..., title="Description of the VC")
#     tags: Optional[list[str]] = Field(None, title="Tags of the VC")
#     embedding: Optional[list[float]] = Field(None, title="Embedding of the VC")