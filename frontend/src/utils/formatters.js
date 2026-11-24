/**
 * Monetary formatting utility for Splitwise AI
 * Standardizes display across all views as ₹X,XXX.XX
 */
export function formatINR(value) {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return '₹0.00';
  }
  const num = Number(value);
  const formatted = num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `₹${formatted}`;
}

export function formatCurrency(value, currency = 'INR') {
  if (value === null || value === undefined || isNaN(Number(value))) {
    return currency === 'USD' ? '$0.00' : '₹0.00';
  }
  const num = Number(value);
  if (currency === 'USD') {
    return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return formatINR(num);
}
