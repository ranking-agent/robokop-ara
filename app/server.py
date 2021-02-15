"""Filter results (top-n)."""
from fastapi import Body, Query
from pydantic import conint
from reasoner_pydantic import Query as ReasonerQuery, Response

from .util import load_example
from .trapi import TRAPI

APP = TRAPI(
    title="Filter results (top-n)",
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
async def filter_results_top_n(
        max_results: conint(ge=0) = Query(..., example=1),
        request: ReasonerQuery = Body(..., example=load_example("query")),
) -> Response:
    """Filter results (top-n)."""
    message = request.message
    if message.results is not None:
        message.results = message.results[:max_results]
    return Response(message=message)
