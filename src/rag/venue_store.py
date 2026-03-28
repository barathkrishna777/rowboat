"""RAG Venue Store — indexes venues and feedback into ChromaDB for semantic search.

Enables:
- "Find places like the bowling alley we went to last time"
- Learning from past feedback to improve recommendations
- Building a venue knowledge base that grows over time
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import chromadb

from src.config import settings
from src.models.event import Venue
from src.models.feedback import PostEventFeedback


_client: chromadb.ClientAPI | None = None
_venue_collection: chromadb.Collection | None = None
_feedback_collection: chromadb.Collection | None = None


def _get_client() -> chromadb.ClientAPI:
    """Lazy-initialize the ChromaDB client."""
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    global _client
    if _client is None:
        persist_dir = settings.chroma_persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_venue_collection() -> chromadb.Collection:
    """Get or create the venue knowledge base collection."""
    global _venue_collection
    if _venue_collection is None:
        client = _get_client()
        _venue_collection = client.get_or_create_collection(
            name="venues",
            metadata={"description": "Venue knowledge base for semantic search"},
        )
    return _venue_collection


def get_feedback_collection() -> chromadb.Collection:
    """Get or create the feedback memory collection."""
    global _feedback_collection
    if _feedback_collection is None:
        client = _get_client()
        _feedback_collection = client.get_or_create_collection(
            name="feedback",
            metadata={"description": "Past outing feedback for learning"},
        )
    return _feedback_collection


# ── Venue Indexing ──────────────────────────────────────────────────


def _venue_to_document(venue: Venue) -> str:
    """Convert a Venue to a searchable text document."""
    parts = [
        f"Name: {venue.name}",
        f"Category: {venue.category.value}",
        f"Tags: {', '.join(venue.categories)}" if venue.categories else "",
        f"Address: {venue.address}" if venue.address else "",
        f"City: {venue.city}" if venue.city else "",
        f"Price: {venue.price_tier.value}" if venue.price_tier else "",
        f"Rating: {venue.rating}/5" if venue.rating else "",
        f"Reviews: {venue.review_count}" if venue.review_count else "",
    ]
    return " | ".join(p for p in parts if p)


def _venue_to_metadata(venue: Venue) -> dict:
    """Extract searchable metadata from a Venue."""
    meta = {
        "name": venue.name,
        "category": venue.category.value,
        "source": venue.source.value,
        "address": venue.address or "",
        "city": venue.city or "",
    }
    if venue.price_tier:
        meta["price_tier"] = venue.price_tier.value
    if venue.rating is not None:
        meta["rating"] = float(venue.rating)
    if venue.review_count is not None:
        meta["review_count"] = int(venue.review_count)
    if venue.categories:
        meta["tags"] = ", ".join(venue.categories[:10])  # ChromaDB metadata limit
    return meta


def index_venues(venues: list[Venue]) -> int:
    """Index a list of venues into the knowledge base. Returns count indexed."""
    collection = get_venue_collection()
    indexed = 0

    for venue in venues:
        doc_id = f"{venue.source.value}_{venue.source_id}"

        # Check if already indexed
        existing = collection.get(ids=[doc_id])
        if existing and existing["ids"]:
            continue  # skip duplicates

        collection.add(
            ids=[doc_id],
            documents=[_venue_to_document(venue)],
            metadatas=[_venue_to_metadata(venue)],
        )
        indexed += 1

    return indexed


def search_similar_venues(
    query: str,
    n_results: int = 10,
    category_filter: str | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    """Search the venue knowledge base semantically.

    Returns list of dicts with: id, document, metadata, distance.
    """
    collection = get_venue_collection()

    if collection.count() == 0:
        return []

    where_filter = {}
    if category_filter:
        where_filter["category"] = category_filter
    if min_rating is not None:
        where_filter["rating"] = {"$gte": min_rating}

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        where=where_filter if where_filter else None,
    )

    venues = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            venues.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })

    return venues


# ── Feedback Indexing ───────────────────────────────────────────────


def index_feedback(
    feedback: PostEventFeedback,
    venue_name: str = "",
    venue_categories: list[str] | None = None,
) -> str:
    """Index a feedback entry for learning from past outings."""
    collection = get_feedback_collection()

    # Build a searchable document from the feedback
    parts = [
        f"Rating: {feedback.overall_rating}/5",
        f"Venue: {venue_name}" if venue_name else "",
        f"Categories: {', '.join(venue_categories)}" if venue_categories else "",
        f"Would repeat: {'Yes' if feedback.would_repeat else 'No'}",
        f"Liked: {', '.join(feedback.liked)}" if feedback.liked else "",
        f"Disliked: {', '.join(feedback.disliked)}" if feedback.disliked else "",
        f"Comments: {feedback.free_text}" if feedback.free_text else "",
    ]
    document = " | ".join(p for p in parts if p)

    metadata = {
        "event_id": feedback.event_id,
        "user_id": feedback.user_id,
        "overall_rating": feedback.overall_rating,
        "would_repeat": feedback.would_repeat,
        "venue_name": venue_name,
    }

    collection.add(
        ids=[feedback.feedback_id],
        documents=[document],
        metadatas=[metadata],
    )

    return feedback.feedback_id


def get_past_preferences(query: str, n_results: int = 5) -> list[dict]:
    """Search past feedback to find what the group liked/disliked before.

    Useful for: "Find something like last time" or avoiding past dislikes.
    """
    collection = get_feedback_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
    )

    entries = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            entries.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })

    return entries


def get_venue_history_summary() -> dict:
    """Get a summary of the venue knowledge base."""
    venue_col = get_venue_collection()
    feedback_col = get_feedback_collection()

    return {
        "total_venues_indexed": venue_col.count(),
        "total_feedback_entries": feedback_col.count(),
    }
