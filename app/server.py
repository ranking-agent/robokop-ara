"""Fill knowledge graph and bind."""
import logging

from bmt import Toolkit
from fastapi import Body
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import httpx
from reasoner_pydantic import Query as ReasonerQuery, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from .config import settings
from .identifiers import map_identifiers
from .util import load_example
from .trapi import TRAPI

BMT = Toolkit()

openapi_kwargs = dict(
    title="ROBOKOP ARA",
    version="2.6.2",
    terms_of_service="N/A",
    translator_component="ARA",
    translator_teams=["Ranking Agent"],
    contact={
        "name": "Kenneth Morton",
        "email": "kenny@covar.com",
        "x-id": "kennethmorton",
        "x-role": "responsible developer",
    },
    openapi_tags=[{"name": "robokop"}],
    trapi_operations=["lookup"],
)

APP = TRAPI(
    **openapi_kwargs,
    docs_url="/",
    root_path_in_servers=False,
)

CORS_OPTIONS = dict(
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
APP.add_middleware(
    CORSMiddleware,
    **CORS_OPTIONS,
)

LOGGER = logging.getLogger(__name__)

@APP.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    LOGGER.exception(exc)
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
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
            f"{settings.robokop_kg}/query",
            json=trapi_query,
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing lookup: {response.text}")

        response = await client.post(
            f"{settings.aragorn_ranker}/omnicorp_overlay",
            json=response.json(),
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing overlay: {response.text}")

        response = await client.post(
            f"{settings.aragorn_ranker}/weight_correctness",
            json=response.json(),
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing weighting: {response.text}")

        response = await client.post(
            f"{settings.aragorn_ranker}/score",
            json=response.json(),
            timeout=None,
        )
        if response.status_code != 200:
            raise HTTPException(500, f"Failed doing scoring: {response.text}")
    return Response(**response.json())
