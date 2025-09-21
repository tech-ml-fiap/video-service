from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.domain.errors import AuthError
from app.adapters.driver.api.controllers import router as api_router

def create_app() -> FastAPI:
    app = FastAPI(title="Video Service")

    @app.exception_handler(AuthError)
    async def auth_error_handler(_, exc: AuthError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(api_router, prefix="/api")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app

app = create_app()
