/**
 * Format a number as Argentine currency (ARS)
 * e.g., 1234567.89 → "ARS 1.234.567,89"
 */
export function formatCurrency(
  amount: number | null | undefined,
  currency: string = 'ARS',
): string {
  if (amount === null || amount === undefined) return '-';
  const formatted = Math.abs(amount).toLocaleString('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const sign = amount < 0 ? '-' : '';
  return `${sign}${currency} ${formatted}`;
}

/**
 * Format a number as Argentine currency without currency symbol
 * e.g., 1234567.89 → "1.234.567,89"
 */
export function formatNumber(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return '-';
  return Math.abs(amount).toLocaleString('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Format a date string (ISO) to Argentine format DD/MM/YYYY
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

/**
 * Format a datetime string to Argentine format DD/MM/YYYY HH:mm
 */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return (
      date.toLocaleDateString('es-AR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }) +
      ' ' +
      date.toLocaleTimeString('es-AR', {
        hour: '2-digit',
        minute: '2-digit',
      })
    );
  } catch {
    return dateStr;
  }
}

/**
 * Format a CUIT with dashes: XX-XXXXXXXX-X
 */
export function formatCUIT(cuit: string | null | undefined): string {
  if (!cuit) return '-';
  // If already formatted, return as is
  if (cuit.includes('-')) return cuit;
  // If 11 digits without dashes, format it
  if (cuit.length === 11) {
    return `${cuit.slice(0, 2)}-${cuit.slice(2, 10)}-${cuit.slice(10)}`;
  }
  return cuit;
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '-';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = bytes / Math.pow(k, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Format a complete invoice number from parts
 */
export function formatInvoiceNumber(
  pointOfSale: string | null,
  invoiceNumber: string | null,
): string {
  if (!pointOfSale && !invoiceNumber) return '-';
  const pv = pointOfSale?.padStart(4, '0') || '????';
  const num = invoiceNumber?.padStart(8, '0') || '????????';
  return `${pv}-${num}`;
}
