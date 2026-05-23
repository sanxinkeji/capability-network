from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.auth.schemas import AuthError, auth_error_response


def register_auth_exception_handlers(app) -> None:
    @app.exception_handler(AuthError)
    async def handle_auth_error(_request: Request, exc: AuthError) -> JSONResponse:
        return auth_error_response(exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(part) for part in err["loc"]), "detail": err["msg"]}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content={
                "code": 40001,
                "message": "invalid request parameters",
                "data": None,
                "errors": errors,
            },
        )
