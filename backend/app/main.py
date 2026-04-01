from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.models import Base
from app.schemas import QueryRequest, QueryResponse
from app.text_to_sql import generate_sql, execute_sql, generate_answer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="MLB StatBat API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
async def query(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Accept a natural language question, convert to SQL, execute, and return results."""
    try:
        sql = await generate_sql(req.question)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="LLM integration not yet configured")

    try:
        rows = await execute_sql(db, sql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL execution error: {e}")

    answer = await generate_answer(req.question, sql, rows)

    return QueryResponse(question=req.question, sql=sql, result=rows, answer=answer)
