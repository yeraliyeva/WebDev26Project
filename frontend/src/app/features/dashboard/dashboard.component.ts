import { Component, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { GameService } from '../../core/services/game.service';
import { Level } from '../../core/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, CommonModule],
  template: `
    <div class="dashboard fade-in">
      <!-- Profile Section -->
      <div class="profile-section" *ngIf="auth.profile() as p">
        <div class="profile-card">
          <div class="avatar-wrapper" *ngIf="p.avatar">
            <img [src]="p.avatar.image_url" [alt]="p.avatar.name" class="avatar-img" />
          </div>
          <div class="profile-info">
            <h2 class="username">{{ p.username }}</h2>
            <div class="stat-row">
              <div class="stat-block">
                <span class="stat-label">score</span>
                <span class="stat-value">{{ p.total_score }}</span>
              </div>
              <div class="stat-block">
                <span class="stat-label">coins</span>
                <span class="stat-value">{{ p.virtual_currency }}</span>
              </div>
              <div class="stat-block">
                <span class="stat-label">best wpm</span>
                <span class="stat-value accent">{{ p.best_wpm | number:'1.0-0' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Level Selection -->
      <div class="levels-section">
        <h3 class="section-title">choose a level</h3>

        <div class="level-grid">
          @for (level of levels(); track level.id) {
            <a [routerLink]="['/play', level.id]"
               class="level-card"
               [class.cat-mode]="level.mode === 'cat_survival'">
              <div class="card-header">
                <span class="mode-tag">
                  {{ level.mode === 'cat_survival' ? 'Cat Survival' : 'Standard' }}
                </span>
                <span class="difficulty-tag">
                  @for (s of getDifficultyStars(level.difficulty); track $index) {
                    <span class="star"></span>
                  }
                </span>
              </div>
              <h4 class="level-title">{{ level.title }}</h4>
              <div class="card-footer">
                <span class="reward">+{{ level.base_reward }} pts</span>
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

  constructor(public auth: AuthService, private game: GameService) { }

  ngOnInit(): void {
    this.game.getLevels().subscribe((data) => this.levels.set(data));
  }

  getDifficultyStars(difficulty: number): number[] {
    return Array(Math.min(difficulty, 5)).fill(0);
  }
}
