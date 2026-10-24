import os
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


api = FastAPI()

API_TOKEN = os.getenv("API_TOKEN")

bearer_security = HTTPBearer(auto_error=False)


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_security
    )
):
    """ Checks that the Bearer token is valid. """

    if API_TOKEN is None:
        raise RuntimeError(
            "The API_TOKEN environment variable is not configured"
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not secrets.compare_digest(
        credentials.credentials,
        API_TOKEN
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"}
        )


@api.get("/")
def get_home(token: None = Depends(verify_token)):
    """ Main endpoint """
    return {
        "message": "My first API"
    }


@api.get("/greetings/{user_name}")
def get_greeting(
    user_name: str,
    token: None = Depends(verify_token)
):
    """ Returns a greeting using the name received in the URL. """
    return {
        "greeting": f"Hello, {user_name}"
    }
