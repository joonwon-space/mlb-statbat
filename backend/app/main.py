import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import QueryRequest, QueryResponse
from app.text_to_sql import generate_sql, execute_sql, generate_answer

logger = logging.getLogger(__name__)

# Rate limiter — keyed on the client IP address.
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic migrations — no create_all() here.
    yield


app = FastAPI(title="MLB StatBat API", version="0.1.0", lifespan=lifespan)

# Attach limiter state and the default 429 error handler.
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,  # type: ignore[arg-type]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query(request: Request, req: QueryRequest, db: AsyncSession = Depends(get_db)):
    """Accept a natural language question, convert to SQL, execute, and return results.

    Rate-limited to 10 requests per minute per IP address.
    """
    try:
        sql = await generate_sql(req.question)
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="LLM integration not yet configured")

    try:
        rows = await execute_sql(db, sql)
    except ValueError as e:
        # SQL guard rejected the query — safe to surface the reason
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("SQL execution failed for question: %r", req.question)
        raise HTTPException(
            status_code=500,
            detail="Failed to execute the generated query. Please try rephrasing your question.",
        )

    answer = await generate_answer(req.question, sql, rows)

    return QueryResponse(question=req.question, sql=sql, result=rows, answer=answer)
