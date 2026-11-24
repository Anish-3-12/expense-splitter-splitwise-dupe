-- V8__fix_rental_categorization_regression.sql
-- Correct vehicle and equipment rentals miscategorized as Housing & Rent
-- Restore 'AWD SUV Rental & Snow Chains' to Travel

UPDATE expenses
SET category_id = (SELECT id FROM expense_categories WHERE name = 'Travel' LIMIT 1)
WHERE LOWER(note) LIKE '%suv rental%'
   OR LOWER(note) LIKE '%car rental%'
   OR LOWER(note) LIKE '%vehicle rental%'
   OR LOWER(note) LIKE '%snow chains%';
