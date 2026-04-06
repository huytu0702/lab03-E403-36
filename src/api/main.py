from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.errors import value_error_handler
from src.api.routes.chat import router as chat_router
from src.api.routes.health import router as health_router
from src.api.routes.metrics import router as metrics_router
from src.api.routes.products import faq_router, router as products_router
from src.api.routes.tools import router as tools_router
from src.api.routes.traces import router as traces_router
from src.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_exception_handler(ValueError, value_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(faq_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(traces_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"app": settings.app_name, "version": settings.version}
