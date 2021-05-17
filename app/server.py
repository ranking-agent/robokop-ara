"""Fill knowledge graph and bind."""
from fastapi import Body
import httpx
from reasoner_pydantic import Query as ReasonerQuery, Response

from .util import load_example
from .trapi import TRAPI

APP = TRAPI(
    title="ROBOKOP ARA",
    version="1.0.0",
    terms_of_service="N/A",
    translator_component="ARA",
    translator_teams=["SRI"],
    contact={
        "name": "Patrick Wang",
        "email": "patrick@covar.com",
        "x-id": "patrickkwang",
        "x-role": "responsible developer",
    },
    openapi_tags=[{"name": "robokop"}]
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
            "https://automat.renci.org/robokopkg/query",
            json=request.dict(),
        )
        response = await client.post(
            "https://aragorn-ranker.renci.org/omnicorp_overlay",
            json=response.json(),
        )
        response = await client.post(
            "https://aragorn-ranker.renci.org/weight_correctness",
            json=response.json(),
        )
        response = await client.post(
            "https://aragorn-ranker.renci.org/score",
            json=response.json(),
        )
    return Response(**response.json())
