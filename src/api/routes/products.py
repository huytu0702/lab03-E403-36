from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.services.faq_service import faq_service
from src.services.product_service import product_service
from src.db.deps import get_db

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(q: str | None = Query(default=None), db: Session = Depends(get_db)):
    return product_service.list_products(db, q)


@router.get("/search")
def search_products(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return product_service.list_products(db, q)


faq_router = APIRouter(prefix="/faqs", tags=["faqs"])


@faq_router.get("")
def list_faqs(db: Session = Depends(get_db)):
    return faq_service.list_faqs(db)
