import os
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import APIKeyHeader


api = FastAPI()

API_KEY = os.getenv("API_KEY")

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_api_key(
    received_api_key: str | None = Depends(api_key_header)
):
    """ Checks that the request contains a valid API key. """

    if API_KEY is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key is not configured on the server"
        )

    if (
        received_api_key is None
        or not secrets.compare_digest(received_api_key, API_KEY)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )


@api.get("/", dependencies=[Depends(verify_api_key)])
def get_home():
    """ Main endpoint """
    return {
        "message": "My first API"
    }


@api.get(
    "/greetings/{user_name}",
    dependencies=[Depends(verify_api_key)]
)
def get_greeting(user_name: str):
    """ Returns a greeting using the name received in the URL. """
    return {
        "greeting": f"Hello, {user_name}"
    }