"""Fill knowledge graph and bind."""
import logging

from bmt import Toolkit
from fastapi import Body
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import httpx
from reasoner_pydantic import Query as ReasonerQuery, Response
from starlette.requests import Request

from .util import load_example
from .trapi import TRAPI

BMT = Toolkit(schema="https://raw.githubusercontent.com/biolink/biolink-model/1.8.2/biolink-model.yaml")
APP = TRAPI(
    title="ROBOKOP ARA",
    version="2.1.0",
    terms_of_service="N/A",
    translator_component="ARA",
    translator_teams=["SRI"],
    contact={
        "name": "Patrick Wang",
        "email": "patrick@covar.com",
        "x-id": "patrickkwang",
        "x-role": "responsible developer",
    },
    openapi_tags=[{"name": "robokop"}],
    trapi_operations=["lookup"],
)


LOGGER = logging.getLogger(__name__)


@APP.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    LOGGER.exception(exc)
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )


async def get_synonyms(curies: list[str]):
    """Get synonyms for CURIE."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://nodenormalization-sri.renci.org/1.1/get_normalized_nodes",
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
                "https://automat.renci.org/robokopkg/1.1/meta_knowledge_graph",
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


@APP.post(
        "/query",
        tags=["reasoner"],
        response_model=Response,
        response_model_exclude_unset=True,
        responses={
            200: {
                "content": {
                    "application/json": {
                        "example": load_example("response")
                    }
                },
            },
        },
)
async def lookup(
        request: ReasonerQuery = Body(..., example=load_example("query")),
) -> Response:
    """Look up answers to the question."""
    trapi_query = request.dict(
        by_alias=True,
        exclude_unset=True,
    )
    try:
        await map_identifiers(trapi_query)
    except KeyError:
        pass
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://automat.renci.org/robokopkg/1.1/query",
            json=trapi_query,
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing lookup: {response.text}")

        response = await client.post(
            "https://aragorn-ranker.renci.org/1.1/omnicorp_overlay",
            json=response.json(),
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing overlay: {response.text}")

        response = await client.post(
            "https://aragorn-ranker.renci.org/1.1/weight_correctness",
            json=response.json(),
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing weighting: {response.text}")

        response = await client.post(
            "https://aragorn-ranker.renci.org/1.1/score",
            json=response.json(),
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing scoring: {response.text}")
    return Response(**response.json())
