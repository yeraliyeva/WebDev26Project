import { Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule, SlicePipe } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { GameService } from '../../core/services/game.service';
import { BalanceResponse, LeaderboardResponse, Level, LevelStatsResponse } from '../../core/models';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

function levelTypeLabel(levelType: Level['level_type']): string {
  return levelType === 'cat_running' ? 'cat survival' : 'standard typing';
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, CommonModule, SlicePipe],
  template: `
    <div class="dashboard fade-in">
      <!-- Profile Section -->
      <div class="profile-section" *ngIf="auth.profile() as p">
        <div class="profile-card">
          <div class="avatar-wrapper" *ngIf="p.profile_image_url">
            <img [src]="p.profile_image_url" [alt]="p.username + ' avatar'" class="avatar-img" />
          </div>
          <div class="profile-info">
            <h2 class="username">{{ p.username }}</h2>
            <div class="stat-row">
              <div class="stat-block">
                <span class="stat-label">score</span>
                <span class="stat-value">{{ todayScore() ?? 0 }}</span>
              </div>
              <div class="stat-block">
                <span class="stat-label">coins</span>
                <span class="stat-value">{{ balance() ?? 0 }}</span>
              </div>
              <div class="stat-block">
                <span class="stat-label">best wpm</span>
                <span class="stat-value accent">{{ (bestWpm() ?? 0) | number:'1.0-0' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Level Selection -->
      <div class="levels-section">
        <h3 class="section-title">choose a level</h3>

        <div *ngIf="loading()" class="loading-state">
          <p>Loading levels...</p>
        </div>

        <div *ngIf="error()" class="error-state">
          <p>{{ error() }}</p>
        </div>

        <div class="level-grid" *ngIf="!loading() && !error()">
          @for (level of levels(); track level.id) {
            <a [routerLink]="['/play', level.id]"
               class="level-card"
               [class.cat-mode]="level.level_type === 'cat_running'">
              <div class="card-header">
                <span class="mode-tag">{{ levelTypeLabel(level.level_type) }}</span>
              </div>
              <p class="level-preview">{{ level.text | slice:0:60 }}…</p>
              <div class="card-footer">
                <span class="reward">+{{ level.cost }} pts</span>
              </div>
            </a>
          }
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  levels = signal<Level[]>([]);
  loading = signal<boolean>(true);
  error = signal<string | null>(null);
  balance = signal<number | null>(null);
  todayScore = signal<number | null>(null);
  bestWpm = signal<number | null>(null);

  constructor(
    public auth: AuthService,
    private game: GameService,
    private http: HttpClient
  ) { }

  levelTypeLabel = levelTypeLabel;

  ngOnInit(): void {
    this.game.getLevels().subscribe({
      next: (data) => {
        this.levels.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Failed to load levels:', err);
        this.error.set('Failed to load levels. Please check your connection or try again later.');
        this.loading.set(false);
      }
    });

    const p = this.auth.profile();
    if (!p) return;

    this.http
      .get<BalanceResponse>(`${environment.apiBase}/balance/${p.id}`)
      .subscribe({ 
        next: (b) => this.balance.set(b.balance),
        error: (err) => console.error('Failed to load balance:', err)
      });

    this.http
      .get<LeaderboardResponse>(`${environment.apiBase}/leaderboard`)
      .subscribe({ 
        next: (lb) => this.todayScore.set(lb.user_score),
        error: (err) => console.error('Failed to load today score:', err)
      });

    this.http
      .get<LevelStatsResponse>(`${environment.apiBase}/level/stats`)
      .subscribe({ 
        next: (s) => this.bestWpm.set(s.best_wpm),
        error: (err) => console.error('Failed to load stats:', err)
      });
  }

}
