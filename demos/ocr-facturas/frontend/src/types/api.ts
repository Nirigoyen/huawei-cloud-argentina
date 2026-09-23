// Paginated response wrapper
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// API error response
export interface ApiError {
  detail: string;
  error_code?: string;
  correlation_id?: string;
}

// Generic API response message
export interface ApiMessage {
  message: string;
}
