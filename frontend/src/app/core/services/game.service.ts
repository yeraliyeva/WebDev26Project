import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AttemptResult, LeaderboardEntry, Level } from '../models';

import { webSocket, WebSocketSubject } from 'rxjs/webSocket';

/**
 * Encapsulates all HTTP communication related to game data:
 * level fetching, attempt submission, and leaderboard retrieval.
 */
@Injectable({ providedIn: 'root' })
export class GameService {
    private readonly base = environment.apiBase;
    private leaderboardWs$: WebSocketSubject<any> | null = null;

    constructor(private http: HttpClient) { }

    getLevels(): Observable<Level[]> {
        return this.http
            .get<{ count: number; results: Level[] }>(`${this.base}/level?start=0&limit=100`)
            .pipe(map((r) => r.results));
    }

    getLevel(id: string): Observable<Level> {
        return this.http.get<Level>(`${this.base}/level/${id}`);
    }

    submitAttempt(payload: {
        level_id: string;
        wpm: number;
    }): Observable<AttemptResult> {
        return this.http.post<AttemptResult>(
            `${this.base}/level/submit`,
            payload
        );
    }

    getLeaderboard(): Observable<LeaderboardEntry[]> {
        return this.http.get<LeaderboardEntry[]>(`${this.base}/leaderboard`);
    }

    connectLeaderboardWS(): Observable<any> {
        if (!this.leaderboardWs$ || this.leaderboardWs$.closed) {
            // Traefik will parse the WS protocol standard port forwarding
            const wsUrl = `ws://localhost:8000/ws`;
            this.leaderboardWs$ = webSocket(wsUrl);
        }
        return this.leaderboardWs$.asObservable();
    }
}
