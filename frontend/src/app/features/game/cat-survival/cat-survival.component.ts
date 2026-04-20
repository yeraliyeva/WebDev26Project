import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  signal,
  HostListener,
  ElementRef,
  ViewChild,
} from '@angular/core';
import { CommonModule, SlicePipe } from '@angular/common';
import { Level } from '../../../core/models';

interface RunnerBranch {
  id: number;
  letter: string;
  x: number;
  lane: number; // 0, 1, 2
  active: boolean;
  broken: boolean;
}

@Component({
  selector: 'app-cat-survival',
  standalone: true,
  imports: [CommonModule, SlicePipe],
  template: `
    <div class="cat-arena fade-in">
      <div class="arena-header">
        <h3 class="arena-title">Cat Survival (Runner)</h3>
        <span class="arena-subtitle">{{ level.text | slice:0:40 }}…</span>
      </div>

      <div class="arena-box" #arenaBox>

        <!-- Dynamic Obstacles (Branches) -->
        @for (branch of branches(); track branch.id) {
          @if (branch.x > -100 && branch.x < 700) {
            <div class="branch"
                 [class.active]="branch.active"
                 [class.broken]="branch.broken"
                 [style.left.px]="branch.x"
                 [style.top.px]="getLaneY(branch.lane)">
              <span class="branch-letter">{{ branch.letter }}</span>
            </div>
          }
        }

        <!-- Running Cat Sprite -->
        <div class="cat-character"
             [class.falling]="fell()"
             [style.top.px]="catY()">
        </div>

      </div>

      <!-- Distance Progress bar -->
      <div class="timer-bar">
        <div class="timer-fill"
             [style.width.%]="progressPercent()"></div>
      </div>

      <!-- Current letter hint -->
      @if (!fell() && !won()) {
        <div class="letter-hint">
          Type: <span class="hint-letter">{{ getCurrentLetter() }}</span>
        </div>
      }

      <!-- Game Over -->
      @if (fell()) {
        <div class="game-over-card fade-in">
          <h2>Oops, try again</h2>
          <p>The cat hit branch {{ currentBranchIndex() }} of {{ totalCount }}</p>
          <button class="action-btn" (click)="restartGame()">Try Again</button>
          <button class="action-btn secondary" (click)="goBack()">Back to Dashboard</button>
        </div>
      }

      <!-- Win -->
      @if (won()) {
        <div class="win-card fade-in">
          <h2>Purrfect Run!</h2>
          <p>The cat successfully reached the end of the forest!</p>
        </div>
      }
    </div>
  `,
  styleUrls: ['./cat-survival.component.scss'],
})
export class CatSurvivalComponent implements OnInit, OnDestroy {
  @Input({ required: true }) level!: Level;
  @Output() completed = new EventEmitter<{ wpm: number; accuracy: number }>();

  @ViewChild('arenaBox') arenaBox?: ElementRef<HTMLDivElement>;

  branches = signal<RunnerBranch[]>([]);
  currentBranchIndex = signal<number>(0);
  progressPercent = signal<number>(0);
  fell = signal<boolean>(false);
  won = signal<boolean>(false);
  
  // Player state
  catY = signal<number>(140);
  
  totalCount = 0;
  private gameLoop: ReturnType<typeof setInterval> | null = null;
  private startTime = 0;
  private errors = 0;

  // Balancing mechanics
  private gameSpeed = 4; // px per tick
  private readonly TICK_MS = 24; 
  private readonly CAT_X = 40; // Collision threshold around left 40
  private lanes = [50, 140, 230];

  ngOnInit(): void {
    this.buildBranches();
    this.startGameLoop();
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }

  getLaneY(laneIdx: number): number {
    return this.lanes[laneIdx];
  }

  getCurrentLetter(): string {
    const idx = this.currentBranchIndex();
    const list = this.branches();
    if (idx < list.length) {
      return list[idx].letter.toUpperCase();
    }
    return '';
  }

  private buildBranches(): void {
    // Generate a long random sequence of letters for the run
    const lettersPool = 'abcdefghijklmnopqrstuvwxyz'.split('');
    // For testing/mocking, make it based on wordcount or just fixed length if content text is small
    const targetLength = this.level.text ? Math.min(this.level.text.length, 50) : 40;
    this.totalCount = targetLength;

    const list: RunnerBranch[] = [];
    let currentX = 300; // First obstacle spawns offscreen slightly
    
    for (let i = 0; i < targetLength; i++) {
        // Pick random lane
        const lane = Math.floor(Math.random() * 3);
        const letter = lettersPool[Math.floor(Math.random() * lettersPool.length)];
        
        list.push({
            id: i,
            letter: letter,
            x: currentX,
            lane: lane,
            active: i === 0,
            broken: false
        });
        
        // Distance spacing shrinks slightly as the game speeds up implicitly
        currentX += Math.floor(200 + Math.random() * 150); 
    }

    this.branches.set(list);
    
    // Position cat initially in the same lane as first branch
    this.catY.set(this.lanes[list[0].lane]);
    this.startTime = Date.now();
  }

  private startGameLoop(): void {
    this.clearTimer();

    this.gameLoop = setInterval(() => {
        if (this.fell() || this.won()) return;

        let collision = false;
        
        // Move all branches left
        this.branches.update(arr => {
            const nextArr = [...arr];
            for (let i = this.currentBranchIndex(); i < nextArr.length; i++) {
                if (!nextArr[i].broken) {
                    nextArr[i] = { ...nextArr[i], x: nextArr[i].x - this.gameSpeed };
                    
                    // Collision check for active branch!
                    if (nextArr[i].active && nextArr[i].x <= this.CAT_X + 24) {
                        collision = true;
                    }
                }
            }
            return nextArr;
        });

        // Compute visual progress bar based on cleared branches
        const pct = (this.currentBranchIndex() / this.totalCount) * 100;
        this.progressPercent.set(pct);

        if (collision) {
            this.triggerFall();
        }

        // Slowly increase speed!
        this.gameSpeed += 0.001; 

    }, this.TICK_MS);
  }

  private triggerFall(): void {
    this.clearTimer();
    this.fell.set(true);
  }

  private clearTimer(): void {
    if (this.gameLoop) {
      clearInterval(this.gameLoop);
      this.gameLoop = null;
    }
  }

  @HostListener('window:keydown', ['$event'])
  onKeyDown(event: KeyboardEvent): void {
    if (this.fell() || this.won()) return;
    if (event.key.length !== 1) return;

    const idx = this.currentBranchIndex();
    const list = this.branches();
    if (idx >= list.length) return;

    const activeBranch = list[idx];

    if (event.key.toLowerCase() === activeBranch.letter) {
      this.advanceCat(idx);
    } else {
      this.errors++;
    }
  }

  private advanceCat(idx: number): void {
    // Break current branch, activate next
    this.branches.update((arr) => {
      const copy = [...arr];
      copy[idx] = { ...copy[idx], active: false, broken: true };
      if (idx + 1 < copy.length) {
        copy[idx + 1] = { ...copy[idx + 1], active: true };
      }
      return copy;
    });

    const next = idx + 1;
    this.currentBranchIndex.set(next);

    if (next >= this.branches().length) {
      this.clearTimer();
      this.progressPercent.set(100);
      this.won.set(true);
      this.emitResult();
      return;
    }

    // Move cat to Y of next branch
    const nextBranch = this.branches()[next];
    this.catY.set(this.lanes[nextBranch.lane]);
  }

  private emitResult(): void {
    const totalSeconds = (Date.now() - this.startTime) / 1000;
    const totalMinutes = totalSeconds / 60;
    const wpm = totalMinutes > 0 ? this.currentBranchIndex() / totalMinutes : 0;
    const totalTyped = this.currentBranchIndex() + this.errors;
    const accuracy =
      totalTyped > 0
        ? ((this.currentBranchIndex() / totalTyped) * 100)
        : 100;

    this.completed.emit({ wpm: Math.round(wpm), accuracy: Math.round(accuracy) });
  }

  restartGame(): void {
    this.fell.set(false);
    this.won.set(false);
    this.currentBranchIndex.set(0);
    this.progressPercent.set(0);
    this.catY.set(140);
    this.errors = 0;
    this.buildBranches();
    this.startGameLoop();
  }

  goBack(): void {
    window.history.back();
  }
}
