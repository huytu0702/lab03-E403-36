from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from src.db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    weight_kg = Column(Numeric(8, 2), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_available = Column(Integer, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    warehouse_name = Column(String(100), default="default", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_type = Column(String(20), nullable=False)
    discount_value = Column(Numeric(12, 2), nullable=False)
    min_order_value = Column(Numeric(12, 2), nullable=False)
    max_discount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ShippingRule(Base):
    __tablename__ = "shipping_rules"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    base_fee = Column(Numeric(12, 2), nullable=False)
    fee_per_kg = Column(Numeric(12, 2), nullable=False)
    estimated_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
