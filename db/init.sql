CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    weight_kg NUMERIC(8, 2) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity_available INTEGER NOT NULL,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    warehouse_name VARCHAR(100) NOT NULL DEFAULT 'default',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, warehouse_name)
);

CREATE TABLE IF NOT EXISTS coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) NOT NULL,
    discount_value NUMERIC(12, 2) NOT NULL,
    min_order_value NUMERIC(12, 2) NOT NULL,
    max_discount NUMERIC(12, 2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shipping_rules (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    base_fee NUMERIC(12, 2) NOT NULL,
    fee_per_kg NUMERIC(12, 2) NOT NULL,
    estimated_days INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (city)
);

CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    topic VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (topic)
);

-- Seed data (idempotent)
INSERT INTO products (sku, name, category, price, weight_kg, description, is_active)
VALUES
    ('IP15-128-BLK', 'iPhone 15', 'phone', 24990000, 0.5, 'Apple iPhone 15 128GB.', TRUE),
    ('SS24-256-GRY', 'Samsung S24', 'phone', 22990000, 0.5, 'Samsung Galaxy S24 256GB.', TRUE),
    ('MBA-M3-13', 'MacBook Air M3', 'laptop', 28990000, 1.3, 'MacBook Air M3 13-inch.', TRUE),
    ('APP2-WHT', 'AirPods Pro 2', 'audio', 5490000, 0.2, 'Apple AirPods Pro 2nd generation.', TRUE)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO inventory (product_id, quantity_available, reserved_quantity, warehouse_name)
VALUES
    ((SELECT id FROM products WHERE sku = 'IP15-128-BLK'), 12, 0, 'default'),
    ((SELECT id FROM products WHERE sku = 'SS24-256-GRY'), 8, 0, 'default'),
    ((SELECT id FROM products WHERE sku = 'MBA-M3-13'), 4, 0, 'default'),
    ((SELECT id FROM products WHERE sku = 'APP2-WHT'), 20, 0, 'default')
ON CONFLICT DO NOTHING;

INSERT INTO coupons (code, discount_type, discount_value, min_order_value, max_discount, is_active)
VALUES
    ('WINNER10', 'percent', 10, 5000000, 3000000, TRUE),
    ('SHIP50', 'fixed', 50000, 1000000, NULL, TRUE),
    ('LUXE5', 'percent', 5, 20000000, NULL, TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO shipping_rules (city, base_fee, fee_per_kg, estimated_days, is_active)
VALUES
    ('Hà Nội', 30000, 10000, 2, TRUE),
    ('TP.HCM', 35000, 12000, 2, TRUE),
    ('Đà Nẵng', 40000, 15000, 3, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO faqs (topic, question, answer, is_active)
VALUES
    ('return_policy', 'Chính sách đổi trả là gì?', 'Bạn có thể đổi trả trong vòng 7 ngày nếu sản phẩm còn nguyên hộp và chưa kích hoạt bảo hành điện tử.', TRUE),
    ('weekend_shipping', 'Shop có giao hàng cuối tuần không?', 'Shop vẫn giao hàng cuối tuần tại Hà Nội và TP.HCM. Một số khu vực khác sẽ xử lý vào ngày làm việc tiếp theo.', TRUE),
    ('warranty', 'Sản phẩm bảo hành bao lâu?', 'Thời gian bảo hành tùy sản phẩm, thường từ 12 đến 24 tháng theo chính sách của hãng.', TRUE)
ON CONFLICT DO NOTHING;
