from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=500,
        description="Natural language baseball stats question (3–500 characters)",
    )


class QueryResponse(BaseModel):
    question: str
    sql: str
    result: list[dict]
    answer: str
