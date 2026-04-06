from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.agent.agent import agent
from src.agent.tools_registry import get_tools
from src.chatbot.chatbot import chatbot
from src.core.mock_provider import MockProvider
from src.db import models
from src.db.session import Base
from src.telemetry.trace_store import trace_store


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", future=True, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        iphone = models.Product(
            sku="IP15-128-BLK",
            name="iPhone 15",
            category="phone",
            price=24990000,
            weight_kg=0.5,
            description="Apple iPhone 15 128GB.",
            is_active=True,
        )
        macbook = models.Product(
            sku="MBA-M3-13",
            name="MacBook Air M3",
            category="laptop",
            price=28990000,
            weight_kg=1.3,
            description="MacBook Air M3 13-inch.",
            is_active=True,
        )
        airpods = models.Product(
            sku="APP2-WHT",
            name="AirPods Pro 2",
            category="audio",
            price=5490000,
            weight_kg=0.2,
            description="Apple AirPods Pro 2nd generation.",
            is_active=True,
        )
        db.add_all([iphone, macbook, airpods])
        db.flush()
        db.add_all(
            [
                models.Inventory(product_id=iphone.id, quantity_available=12, reserved_quantity=0, warehouse_name="default"),
                models.Inventory(product_id=macbook.id, quantity_available=4, reserved_quantity=0, warehouse_name="default"),
                models.Inventory(product_id=airpods.id, quantity_available=20, reserved_quantity=0, warehouse_name="default"),
                models.Coupon(
                    code="WINNER10",
                    discount_type="percent",
                    discount_value=10,
                    min_order_value=5000000,
                    max_discount=3000000,
                    is_active=True,
                ),
                models.Coupon(
                    code="SHIP50",
                    discount_type="fixed",
                    discount_value=50000,
                    min_order_value=1000000,
                    max_discount=None,
                    is_active=True,
                ),
                models.ShippingRule(city="Hà Nội", base_fee=30000, fee_per_kg=10000, estimated_days=2, is_active=True),
                models.ShippingRule(city="TP.HCM", base_fee=35000, fee_per_kg=12000, estimated_days=2, is_active=True),
                models.ShippingRule(city="Đà Nẵng", base_fee=40000, fee_per_kg=15000, estimated_days=3, is_active=True),
                models.FAQ(
                    topic="return_policy",
                    question="Chính sách đổi trả là gì?",
                    answer="Bạn có thể đổi trả trong vòng 7 ngày nếu sản phẩm còn nguyên hộp và chưa kích hoạt bảo hành điện tử.",
                    is_active=True,
                ),
                models.FAQ(
                    topic="weekend_shipping",
                    question="Shop có giao hàng cuối tuần không?",
                    answer="Shop vẫn giao hàng cuối tuần tại Hà Nội và TP.HCM. Một số khu vực khác sẽ xử lý vào ngày làm việc tiếp theo.",
                    is_active=True,
                ),
            ]
        )
        db.commit()

    import src.db.deps as db_deps
    import src.db.session as db_session
    import src.chatbot.chatbot as chatbot_module
    import src.agent.tools_registry as tools_registry
    import src.agent.parser as parser_module

    monkeypatch.setattr(db_session, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(db_deps, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(chatbot_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(tools_registry, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(parser_module, "SessionLocal", TestingSessionLocal)

    chatbot.llm = MockProvider(model_name="test-mock")
    agent.llm = MockProvider(model_name="test-mock")
    agent.tools = get_tools()

    trace_dir = tmp_path / "traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_store.base_dir = str(trace_dir)

    return TestClient(app)
