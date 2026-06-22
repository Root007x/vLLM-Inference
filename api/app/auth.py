import hmac

from fastapi import Header, HTTPException
from .config import settings


def auth(x_api_key: str = Header()):
    if not hmac.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API Key")

    return True
