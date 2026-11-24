-- V6__add_receipt_raw_ocr_and_validation.sql
-- Preserve raw OCR text, currency evidence, validation status, and ambiguity flags

ALTER TABLE receipts ADD COLUMN raw_ocr_text TEXT NULL;
ALTER TABLE receipts ADD COLUMN currency_symbol VARCHAR(10) NULL;
ALTER TABLE receipts ADD COLUMN validation_status VARCHAR(50) NULL DEFAULT 'RECONCILED';
ALTER TABLE receipts ADD COLUMN discrepancy_amount DECIMAL(19,2) NULL DEFAULT 0.00;

ALTER TABLE receipt_items ADD COLUMN is_ambiguous BOOLEAN DEFAULT FALSE;
ALTER TABLE receipt_items ADD COLUMN ambiguity_reason VARCHAR(255) NULL;
