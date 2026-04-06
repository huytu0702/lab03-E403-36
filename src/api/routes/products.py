from fastapi import APIRouter, Query

from src.services.faq_service import faq_service
from src.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(q: str | None = Query(default=None)):
    return product_service.list_products(q)


@router.get("/search")
def search_products(q: str = Query(..., min_length=1)):
    return product_service.list_products(q)


faq_router = APIRouter(prefix="/faqs", tags=["faqs"])


@faq_router.get("")
def list_faqs():
    return faq_service.list_faqs()
