BENCHMARK_CASES = [
    {
        "id": "case_1",
        "title": "FAQ đổi trả",
        "message": "Chính sách đổi trả là gì?",
        "expected": "Trả lời đúng theo FAQ đổi trả, không bịa thêm chính sách.",
        "expected_winner": "v1",
    },
    {
        "id": "case_2",
        "title": "FAQ giao hàng cuối tuần",
        "message": "Shop có giao hàng cuối tuần không?",
        "expected": "Trả lời đúng theo FAQ giao hàng cuối tuần.",
        "expected_winner": "v1",
    },
    {
        "id": "case_3",
        "title": "Quote nhiều bước",
        "message": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?",
        "expected": "Lấy giá, kiểm kho, áp coupon và tính ship để ra tổng cuối cùng.",
        "expected_winner": "v2",
    },
    {
        "id": "case_4",
        "title": "Kiểm hàng và tính giá",
        "message": "MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?",
        "expected": "Trả đúng stock, giá sản phẩm và chi phí ship.",
        "expected_winner": "v2",
    },
    {
        "id": "case_5",
        "title": "Edge case coupon sai",
        "message": "Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.",
        "expected": "Phát hiện coupon sai, không bịa giảm giá, vẫn trả subtotal và shipping nếu có thể.",
        "expected_winner": "v2",
    },
]


AUXILIARY_CASES = [
    {
        "id": "aux_1",
        "title": "Out-of-domain guard",
        "message": "Thời tiết hôm nay thế nào?",
        "expected": "Trả response blocked thân thiện, không gọi LLM/tool và gắn OUT_OF_DOMAIN.",
        "expected_status": "blocked",
        "expected_error_code": "OUT_OF_DOMAIN",
    },
]
