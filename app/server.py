"""Fill knowledge graph and bind."""
from fastapi import Body
from fastapi.exceptions import HTTPException
import httpx
from reasoner_pydantic import Query as ReasonerQuery, Response

from .util import load_example
from .trapi import TRAPI

APP = TRAPI(
    title="ROBOKOP ARA",
    version="2.0.0",
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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://automat.renci.org/robokopkg/1.1/query",
            json=request.dict(
                by_alias=True,
                exclude_unset=True,
            ),
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
