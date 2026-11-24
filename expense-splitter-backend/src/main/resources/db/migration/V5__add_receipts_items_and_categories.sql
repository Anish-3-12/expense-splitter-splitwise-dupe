-- V5__add_receipts_items_and_categories.sql
-- Additive migration for Splitwise AI: categories, receipts, receipt items, expense items, and AI insights

-- 1. Expense Categories Table
CREATE TABLE IF NOT EXISTS expense_categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    icon VARCHAR(50),
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial categories
INSERT INTO expense_categories (name, icon, description) VALUES
('Food & Dining', 'restaurant', 'Restaurants, cafes, food delivery, and dining out'),
('Groceries', 'shopping_cart', 'Supermarket, produce, household supplies'),
('Transportation', 'directions_car', 'Cabs, fuel, public transit, flights, parking'),
('Entertainment', 'movie', 'Movies, concerts, games, streaming subscriptions'),
('Shopping', 'shopping_bag', 'Clothing, electronics, personal items'),
('Utilities', 'power', 'Electricity, water, gas, internet, mobile bills'),
('Travel', 'flight', 'Hotels, vacation expenses, tours, booking fees'),
('Healthcare', 'local_hospital', 'Medical visits, pharmacy, insurance, wellness'),
('Other', 'category', 'Miscellaneous or uncategorized expenses');

-- 2. Add category_id to expenses table
ALTER TABLE expenses ADD COLUMN category_id BIGINT NULL;
ALTER TABLE expenses ADD CONSTRAINT fk_expenses_category FOREIGN KEY (category_id) REFERENCES expense_categories(id) ON DELETE SET NULL;
CREATE INDEX idx_expenses_category ON expenses(category_id);

-- 3. Receipts Table
CREATE TABLE IF NOT EXISTS receipts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    uploaded_by BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'UPLOADED', -- UPLOADED, PROCESSING, EXTRACTED, CONFIRMED, FAILED
    total_amount DECIMAL(19,2) NULL,
    subtotal DECIMAL(19,2) NULL,
    tax DECIMAL(19,2) NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    merchant_name VARCHAR(255) NULL,
    receipt_date VARCHAR(50) NULL,
    expense_id BIGINT NULL,
    error_message VARCHAR(1000) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_receipts_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    CONSTRAINT fk_receipts_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_receipts_expense FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE SET NULL
);
CREATE INDEX idx_receipts_group ON receipts(group_id);

-- 4. Receipt Line Items Table (extracted from receipt OCR / AI)
CREATE TABLE IF NOT EXISTS receipt_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    receipt_id BIGINT NOT NULL,
    line_number INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1.00,
    unit_price DECIMAL(19,2) NOT NULL,
    line_total DECIMAL(19,2) NOT NULL,
    confidence DECIMAL(5,2) DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_receipt_items_receipt FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);
CREATE INDEX idx_receipt_items_receipt ON receipt_items(receipt_id);

-- 5. Expense Line Items Table (for itemized splitting)
CREATE TABLE IF NOT EXISTS expense_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    expense_id BIGINT NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1.00,
    unit_price DECIMAL(19,2) NOT NULL,
    line_total DECIMAL(19,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_expense_items_expense FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
);
CREATE INDEX idx_expense_items_expense ON expense_items(expense_id);

-- 6. Expense Item Allocations Table (which users share which specific item)
CREATE TABLE IF NOT EXISTS expense_item_shares (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    expense_item_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    share_amount DECIMAL(19,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_item_shares_item FOREIGN KEY (expense_item_id) REFERENCES expense_items(id) ON DELETE CASCADE,
    CONSTRAINT fk_item_shares_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_item_shares_item ON expense_item_shares(expense_item_id);

-- 7. Expense AI Insights / Anomaly Detection Results Table
CREATE TABLE IF NOT EXISTS expense_ai_insights (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    group_id BIGINT NOT NULL,
    expense_id BIGINT NULL,
    insight_type VARCHAR(50) NOT NULL, -- ANOMALY, TREND, SPENDING_SPIKE, RECOMMENDATION
    severity VARCHAR(20) NOT NULL DEFAULT 'INFO', -- INFO, LOW, MEDIUM, HIGH
    summary VARCHAR(500) NOT NULL,
    details_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_insights_group FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    CONSTRAINT fk_insights_expense FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
);
CREATE INDEX idx_insights_group ON expense_ai_insights(group_id);
