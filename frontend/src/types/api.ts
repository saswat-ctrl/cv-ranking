// API Type Definitions
// Centralized types for all API requests and responses

import { AxiosError } from 'axios'

// ============================================================================
// User & Auth Types
// ============================================================================

export interface User {
    id: string
    email: string
    full_name: string
    created_at: string
}

export interface LoginRequest {
    email: string
    password: string
}

export interface SignupRequest {
    email: string
    password: string
    full_name: string
}

export interface AuthResponse {
    access_token: string
    token_type: string
}

// ============================================================================
// Job Types
// ============================================================================

export interface Job {
    id: string
    title: string
    user_id: string
    file_url: string
    extracted_text: string
    extraction_status: string
    extraction_error: string | null
    extraction_duration: number
    file_type: string
    file_size: number
    status: 'open' | 'closed' | 'draft'
    created_at: string
    updated_at: string
    candidate_count?: number
}

export interface JobCreate {
    title: string
    description: string
}

export interface JobUpdate {
    title?: string
    description?: string
    status?: 'open' | 'closed' | 'draft'
}

// ============================================================================
// Candidate Types
// ============================================================================

export interface Candidate {
    id: string
    job_id: string
    name: string
    email: string
    parsed_phone: string | null
    cv_file_url: string
    extracted_text: string
    parsed_skills: string[]
    extraction_status: string
    extraction_error: string | null
    extraction_duration: number
    file_type: string
    file_size: number
    is_readable: boolean
    ranking_score: number | null
    ranking_explanation: string | null
    user_score: number | null
    created_at: string
    updated_at: string
}

export interface CandidateUpdate {
    user_score?: number
}

export interface ImportCandidatesRequest {
    source_job_id: string
    candidate_ids: string[]
}

export interface ImportCandidatesResponse {
    imported: number
    skipped: number
    message: string
}

// ============================================================================
// Pagination Types
// ============================================================================

export interface PaginatedResponse<T> {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface CandidateQueryParams {
    page?: number
    page_size?: number
    sort_by?: 'name' | 'email' | 'ranking_score' | 'created_at'
    sort_order?: 'asc' | 'desc'
}

// ============================================================================
// Ranking Types
// ============================================================================

export interface RankingResult {
    job_id: string
    total_candidates: number
    ranked_count: number
    unreadable_count: number
    error_count: number
    duration: number
    message: string
}

// ============================================================================
// Error Types
// ============================================================================

export interface ApiErrorDetail {
    detail: string
}

export interface ApiValidationError {
    loc: (string | number)[]
    msg: string
    type: string
}

export interface ApiError {
    detail: string | ApiValidationError[]
}

// Type guard for API errors
export function isApiError(error: unknown): error is AxiosError<ApiError> {
    return (
        typeof error === 'object' &&
        error !== null &&
        'isAxiosError' in error &&
        error.isAxiosError === true
    )
}

// Helper to extract error message
export function getErrorMessage(error: unknown): string {
    if (isApiError(error)) {
        const responseData = error.response?.data as any

        // Format 1: Standard FastAPI format - {detail: string}
        if (typeof responseData?.detail === 'string') {
            return responseData.detail
        }

        // Format 2: FastAPI validation errors - {detail: [{loc, msg, type}]}
        if (Array.isArray(responseData?.detail)) {
            return responseData.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
        }

        // Format 3: Ranking service format - {detail: {error_code, message, details}}
        // (This happens when backend does: raise HTTPException(detail=result_object))
        if (typeof responseData?.detail === 'object' && responseData.detail !== null) {
            // Try to extract message from nested object
            const nested = responseData.detail as any
            if (typeof nested.message === 'string') {
                return nested.message
            }
            if (typeof nested.error_code === 'string' && typeof nested.details === 'string') {
                return `${nested.error_code}: ${nested.details}`
            }
        }

        // Format 4: Backend custom format - {message: string}
        if (typeof responseData?.message === 'string') {
            return responseData.message
        }

        // Format 5: Direct error_code format - {error_code, message, details}
        if (typeof responseData?.error_code === 'string' && typeof responseData?.message === 'string') {
            return responseData.message
        }

        // Fallback: If we have any data, stringify it (but keep it readable)
        if (responseData) {
            // Try to extract any string value from the response
            const stringValue = Object.values(responseData).find(v => typeof v === 'string')
            if (stringValue) {
                return String(stringValue)
            }
            // Last resort: stringify the object
            return JSON.stringify(responseData)
        }
    }

    if (error instanceof Error) {
        return error.message
    }

    return 'An unexpected error occurred'
}
