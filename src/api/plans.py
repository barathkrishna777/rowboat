"""Plan generation API endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from src.agents.search_agent import SearchResult, run_search

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(description="What kind of outing to search for")
    location: str = Field(default="Pittsburgh, PA", description="Location to search")
    max_results: int = Field(default=10, ge=1, le=50)


@router.post("/search", response_model=SearchResult)
async def search_venues(request: SearchRequest):
    """Search for venues and events using the AI search agent."""
    try:
        result = await run_search(
            query=request.query,
            location=request.location,
            max_results=request.max_results,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
