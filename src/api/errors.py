from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from src.schemas.api import ErrorResponse


ERROR_HTTP_STATUS: dict[str, int] = {
    "PRODUCT_NOT_FOUND": 404,
    "INSUFFICIENT_STOCK": 409,
    "COUPON_NOT_FOUND": 404,
    "COUPON_INVALID": 400,
    "SHIPPING_RULE_NOT_FOUND": 404,
}


def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    error_code = str(exc)
    status_code = ERROR_HTTP_STATUS.get(error_code, 400)
    payload = ErrorResponse(error_code=error_code, message="Request failed.").model_dump()
    return JSONResponse(status_code=status_code, content=payload)

