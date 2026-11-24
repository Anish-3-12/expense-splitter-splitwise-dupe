-- V7__add_rent_housing_category.sql
-- Add Housing & Rent category and reassign rent expenses to it

INSERT INTO expense_categories (name, icon, description)
SELECT 'Housing & Rent', 'home', 'Apartment rent, lease payments, mortgage, maintenance, housing fees'
WHERE NOT EXISTS (
    SELECT 1 FROM expense_categories WHERE name = 'Housing & Rent'
);

UPDATE expenses
SET category_id = (SELECT id FROM expense_categories WHERE name = 'Housing & Rent' LIMIT 1)
WHERE LOWER(note) LIKE '%rent%' OR LOWER(note) LIKE '%apartment%';
