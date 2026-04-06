from fastapi import APIRouter
from pydantic import BaseModel

from src.services.quote_service import quote_service

router = APIRouter(prefix="/tools", tags=["tools"])


class PriceRequest(BaseModel):
    product_name: str


class StockRequest(BaseModel):
    product_name: str
    quantity: int


class CouponRequest(BaseModel):
    coupon_code: str
    order_subtotal: int


class ShippingRequest(BaseModel):
    destination_city: str
    total_weight_kg: float


@router.post("/get-product-price")
def get_product_price(request: PriceRequest):
    return quote_service.get_price(request.product_name)


@router.post("/check-stock")
def check_stock(request: StockRequest):
    return quote_service.check_stock(request.product_name, request.quantity)


@router.post("/get-coupon-discount")
def get_coupon_discount(request: CouponRequest):
    return quote_service.get_coupon_discount(request.coupon_code, request.order_subtotal)


@router.post("/calc-shipping")
def calc_shipping(request: ShippingRequest):
    return quote_service.calc_shipping(request.destination_city, request.total_weight_kg)
