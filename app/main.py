from fastapi import FastAPI
from app.adapters.driver.api.controllers import router as api_router
from fastapi.responses import RedirectResponse

app = FastAPI(title="SOAT10 - Video Service (Hexagonal)", version="0.2.0")
app.include_router(api_router)

@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/docs")

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}