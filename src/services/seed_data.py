PRODUCTS = [
    {
        "id": 1,
        "sku": "IP15-128-BLK",
        "name": "iPhone 15",
        "category": "phone",
        "price": 24990000,
        "weight_kg": 0.5,
        "stock": 12,
        "description": "Apple iPhone 15 128GB.",
    },
    {
        "id": 2,
        "sku": "SS24-256-GRY",
        "name": "Samsung S24",
        "category": "phone",
        "price": 22990000,
        "weight_kg": 0.5,
        "stock": 8,
        "description": "Samsung Galaxy S24 256GB.",
    },
    {
        "id": 3,
        "sku": "MBA-M3-13",
        "name": "MacBook Air M3",
        "category": "laptop",
        "price": 28990000,
        "weight_kg": 1.3,
        "stock": 4,
        "description": "MacBook Air M3 13-inch.",
    },
    {
        "id": 4,
        "sku": "APP2-WHT",
        "name": "AirPods Pro 2",
        "category": "audio",
        "price": 5490000,
        "weight_kg": 0.2,
        "stock": 20,
        "description": "Apple AirPods Pro 2nd generation.",
    },
]

COUPONS = [
    {"code": "WINNER10", "discount_type": "percent", "discount_value": 10, "min_order_value": 5000000, "max_discount": 3000000, "is_active": True},
    {"code": "SHIP50", "discount_type": "fixed", "discount_value": 50000, "min_order_value": 1000000, "max_discount": None, "is_active": True},
    {"code": "LUXE5", "discount_type": "percent", "discount_value": 5, "min_order_value": 20000000, "max_discount": None, "is_active": True},
]

SHIPPING_RULES = [
    {"city": "Hà Nội", "base_fee": 30000, "fee_per_kg": 10000, "estimated_days": 2},
    {"city": "TP.HCM", "base_fee": 35000, "fee_per_kg": 12000, "estimated_days": 2},
    {"city": "Đà Nẵng", "base_fee": 40000, "fee_per_kg": 15000, "estimated_days": 3},
]

FAQS = [
    {
        "id": 1,
        "topic": "return_policy",
        "question": "Chính sách đổi trả là gì?",
        "answer": "Bạn có thể đổi trả trong vòng 7 ngày nếu sản phẩm còn nguyên hộp và chưa kích hoạt bảo hành điện tử.",
    },
    {
        "id": 2,
        "topic": "weekend_shipping",
        "question": "Shop có giao hàng cuối tuần không?",
        "answer": "Shop vẫn giao hàng cuối tuần tại Hà Nội và TP.HCM. Một số khu vực khác sẽ xử lý vào ngày làm việc tiếp theo.",
    },
    {
        "id": 3,
        "topic": "warranty",
        "question": "Sản phẩm bảo hành bao lâu?",
        "answer": "Thời gian bảo hành tùy sản phẩm, thường từ 12 đến 24 tháng theo chính sách của hãng.",
    },
]
