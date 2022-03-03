"""Utilities for handling identifiers."""
from typing import List
from fastapi.exceptions import HTTPException
import httpx

from .config import settings


async def get_synonyms(curies: List[str]):
    """Get synonyms for CURIE."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.node_norm}/get_normalized_nodes",
            json={"curies": curies},
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed synonymizing node ids: {response.text}")

    return {
        key: {
            "synonyms": [eq_id["identifier"] for eq_id in value["equivalent_identifiers"]],
            "categories": value["type"],
        }
        for key, value in response.json().items()
    }


PREFERRED_PREFIXES = None
async def get_preferred_prefixes():
    """Get preferred prefixes from automat/robokopkg."""
    global PREFERRED_PREFIXES
    if PREFERRED_PREFIXES is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.robokop_kg}/meta_knowledge_graph",
            )
            if response.status_code != 200:
                raise HTTPException(500, f"Failed finding preferred prefixes: {response.text}")
        meta_kg = response.json()
        PREFERRED_PREFIXES = {
            category: value["id_prefixes"]
            for category, value in meta_kg["nodes"].items()
        }
    return PREFERRED_PREFIXES


async def map_identifiers(trapi_query):
    """Map identifiers to preferred set."""
    preferred_prefixes = await get_preferred_prefixes()
    curies = [
        curie
        for node in trapi_query["message"]["query_graph"]["nodes"].values()
        for curie in node.get("ids", [])
    ]
    synonyms = await get_synonyms(curies)
    for node in trapi_query["message"]["query_graph"]["nodes"].values():
        if not node.get("ids"):
            continue
        node["ids"] = [
            next(
                synonym
                for synonym in synonyms[curie]["synonyms"]
                if any(
                    synonym.startswith(prefix)
                    for category in synonyms[curie]["categories"]
                    for prefix in preferred_prefixes[category]
                )
            )
            for curie in node["ids"]
        ]
