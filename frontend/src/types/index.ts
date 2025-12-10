export interface Job {
    id: string;
    title: string;
    file_url?: string;
    extracted_text?: string;
    status: 'OPEN' | 'CLOSED' | 'ARCHIVED';
    created_at: string;
    candidate_count?: number;
}

export interface Candidate {
    id: string;
    job_id: string;
    name: string;
    email: string;
    cv_file_url: string;
    extracted_text?: string;
    parsed_skills?: string[];
    ranking_score?: number;
    semantic_score?: number;
    keyword_score?: number;
    ranking_reasoning?: string;
    is_readable: boolean;
    created_at: string;
}

export interface RankingResult {
    success: boolean;
    job_id: string;
    total_candidates: number;
    ranked_count: number;
    duration_seconds: number;
    warnings?: { code: string; message: string }[];
}

export interface User {
    id: string;
    email: string;
    name?: string;
}
