export interface Avatar {
    id: string;
    image_url: string;
}

export interface Profile {
    id: string; // UUID from auth_service
    username: string;
    email: string;
    profile_image_url: string | null;
    created_at: string;
    updated_at: string;
}

export interface Level {
    id: string; // UUID
    text: string;
    cost: number;
    goal_wpm: number;
    level_type: 'default' | 'cat_running';
    created_at: string;
    updated_at: string;
}

export interface AttemptResult {
    id: string; // UUID
    level_id: string;
    user_id: string;
    wpm: number;
    rewarded_credits: number;
    created_at: string;
}

export interface LeaderboardEntry {
    id: string; // UUID
    username: string;
    avatar_url: string;
    total_score: number;
    best_wpm: number;
}

export interface AuthTokens {
    user_id: string;
    access_token: string;
    refresh_token: string;
}

export interface RefreshResponse {
    access_token: string;
}

export interface BalanceResponse {
    id: string;
    user_id: string;
    balance: number;
    updated_at: string;
}

export interface LeaderboardResponse {
    top: Array<{ place: number; user_id: string; score: number }>;
    user_place: number | null;
    user_score: number;
}

export interface LevelStatsResponse {
    user_id: string;
    best_wpm: number;
}

export interface Branch {
    id: number;
    letter: string;
    active: boolean;
    broken: boolean;
}
