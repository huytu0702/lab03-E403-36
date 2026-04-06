from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db.deps import get_db
from src.services.quote_service import quote_service

router = APIRouter(prefix="/tools", tags=["tools"])


class PriceRequest(BaseModel):
    product_name: str = Field(..., min_length=1)


class StockRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class CouponRequest(BaseModel):
    coupon_code: str = Field(..., min_length=1)
    order_subtotal: int = Field(..., ge=0)


class ShippingRequest(BaseModel):
    destination_city: str = Field(..., min_length=1)
    total_weight_kg: float = Field(..., gt=0)


@router.post("/get-product-price")
def get_product_price(request: PriceRequest, db: Session = Depends(get_db)):
    return quote_service.get_price(db, request.product_name)


@router.post("/check-stock")
def check_stock(request: StockRequest, db: Session = Depends(get_db)):
    return quote_service.check_stock(db, request.product_name, request.quantity)


@router.post("/get-coupon-discount")
def get_coupon_discount(request: CouponRequest, db: Session = Depends(get_db)):
    return quote_service.get_coupon_discount(db, request.coupon_code, request.order_subtotal)


@router.post("/calc-shipping")
def calc_shipping(request: ShippingRequest, db: Session = Depends(get_db)):
    return quote_service.calc_shipping(db, request.destination_city, request.total_weight_kg)
