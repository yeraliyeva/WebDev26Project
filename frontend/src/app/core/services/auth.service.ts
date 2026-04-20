import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap, catchError, throwError, switchMap, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthTokens, Profile } from '../models';
import { normalizeStorageUrl } from '../utils/storage-url';

/**
 * Manages authentication state: JWT tokens, user profile caching,
 * login, registration, and logout.
 *
 * Tokens are kept in localStorage only — never in Angular state —
 * so they survive page refreshes without introducing a global mutable
 * variable.  A reactive `profile` signal is exposed for components
 * that need to react to identity changes.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
    private readonly base = `${environment.apiBase}/auth`;

    readonly profile = signal<Profile | null>(null);
    readonly isLoggedIn = computed(() => this.profile() !== null);
    readonly isReady = signal(false);

    constructor(private http: HttpClient, private router: Router) {
        if (this.getAccessToken()) {
            this.loadProfile().subscribe({
                next: () => this.isReady.set(true),
                error: () => {
                    this.logout();
                    this.isReady.set(true);
                }
            });
        } else {
            this.isReady.set(true);
        }
    }

    getAccessToken(): string | null {
        return localStorage.getItem('access_token');
    }

    private setTokens(tokens: AuthTokens): void {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
    }

    login(username: string, password: string) {
        return this.http
            .post<AuthTokens>(`${this.base}/login`, { login: username, password })
            .pipe(
                tap((tokens) => this.setTokens(tokens)),
                switchMap(() => this.loadProfile())
            );
    }

    register(payload: {
        username: string;
        email: string;
        password: string;
        profile_image?: string | null;
    }) {
        return this.http.post(`${this.base}/registration`, payload);
    }

    loadProfile() {
        return this.http.get<Profile>(`${this.base}/me`).pipe(
            map((p) => ({ ...p, profile_image_url: normalizeStorageUrl(p.profile_image_url) })),
            tap((profile) => this.profile.set(profile)),
            catchError((err) => {
                this.profile.set(null);
                return throwError(() => err);
            })
        );
    }

    getPublicProfile(id: string) {
        return this.http.get<Profile>(`${this.base}/users/${id}`).pipe(
            map((p) => ({ ...p, profile_image_url: normalizeStorageUrl(p.profile_image_url) }))
        );
    }

    logout(): void {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        this.profile.set(null);
        this.router.navigate(['/login']);
    }
}
