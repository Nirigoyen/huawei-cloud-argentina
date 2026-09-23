/** Maximum file size in bytes (15 MB) */
export const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024;

/** Allowed file extensions */
export const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];

/** Allowed MIME types */
export const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'image/svg+xml',
];

/**
 * Validate file extension
 */
export function validateFileExtension(filename: string): boolean {
  const ext = filename.toLowerCase().slice(filename.lastIndexOf('.'));
  return ALLOWED_EXTENSIONS.includes(ext);
}

/**
 * Validate file MIME type
 */
export function validateMimeType(mimeType: string): boolean {
  return ALLOWED_MIME_TYPES.includes(mimeType);
}

/**
 * Validate file size
 */
export function validateFileSize(size: number): boolean {
  return size > 0 && size <= MAX_FILE_SIZE_BYTES;
}

/**
 * Validate filename for path traversal
 */
export function validateFileName(filename: string): boolean {
  if (filename.includes('..')) return false;
  if (filename.includes('\\')) return false;
  if (filename.includes('//')) return false;
  if (filename.length > 255) return false;
  return true;
}

/**
 * Full file validation - returns error message or null if valid
 */
export function validateFile(file: File): string | null {
  if (!validateFileName(file.name)) {
    return 'Nombre de archivo inválido.';
  }
  if (!validateFileExtension(file.name)) {
    return `Tipo de archivo no soportado. Permitidos: ${ALLOWED_EXTENSIONS.join(', ')}`;
  }
  if (!validateFileSize(file.size)) {
    return `El archivo supera el tamaño máximo de 15 MB.`;
  }
  return null;
}
