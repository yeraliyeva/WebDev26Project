import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { GameService } from '../../../core/services/game.service';
import { Level } from '../../../core/models';
import { StandardTypingComponent } from '../standard/standard-typing.component';
import { CatSurvivalComponent } from '../cat-survival/cat-survival.component';

@Component({
  selector: 'app-game-play',
  standalone: true,
  imports: [CommonModule, StandardTypingComponent, CatSurvivalComponent],
  template: `
    <div class="game-play">
      @if (level()) {
        @if (level()!.mode === 'standard') {
          <app-standard-typing
            [level]="level()!"
            (completed)="onCompleted($event)"
          />
        } @else {
          <app-cat-survival
            [level]="level()!"
            (completed)="onCompleted($event)"
          />
        }

        @if (result()) {
          <div class="result-overlay">
            <div class="result-card fade-in">
              <h2>Level Complete</h2>
              <div class="result-stats">
                <div class="result-stat">
                  <span class="result-label">wpm</span>
                  <span class="result-value">{{ result()!.wpm | number:'1.0-0' }}</span>
                </div>
                <div class="result-stat">
                  <span class="result-label">accuracy</span>
                  <span class="result-value">{{ result()!.accuracy | number:'1.0-1' }}%</span>
                </div>
                <div class="result-stat">
                  <span class="result-label">earned</span>
                  <span class="result-value accent">+{{ result()!.earned_score }}</span>
                </div>
                <div class="result-stat">
                  <span class="result-label">total score</span>
                  <span class="result-value">{{ result()!.new_total_score }}</span>
                </div>
              </div>
              <button class="action-btn" (click)="clearResult()">Back to Dashboard</button>
            </div>
          </div>
        }
      } @else if (error()) {
        <div class="error-card fade-in">
          <h2>Error</h2>
          <p>{{ error() }}</p>
        </div>
      } @else {
        <div class="loading-state">
          <p>Loading level...</p>
        </div>
      }
    </div>
  `,
  styleUrls: ['./game-play.component.scss'],
})
export class GamePlayComponent implements OnInit {
  level = signal<Level | null>(null);
  result = signal<any>(null);
  error = signal<string>('');

  constructor(
    private route: ActivatedRoute,
    private game: GameService
  ) { }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.game.getLevel(id).subscribe({
      next: (l) => this.level.set(l),
      error: () => this.error.set('Level not found.'),
    });
  }

  onCompleted(payload: { wpm: number; accuracy: number }): void {
    const level = this.level()!;
    this.game
      .submitAttempt({ level_id: level.id, ...payload })
      .subscribe({
        next: (res) => this.result.set(res),
        error: () => alert('Score submission failed.'),
      });
  }

  clearResult(): void {
    this.result.set(null);
    window.history.back();
  }
}
