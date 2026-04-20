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
    AfterViewInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Level } from '../../../core/models';
import { generateLesson } from './typing-dictionary';

@Component({
    selector: 'app-standard-typing',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div class="typing-arena" (click)="focus()">

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="mini-stat">
          <span class="label">wpm</span>
          <span class="val">{{ liveWpm() }}</span>
        </div>
        <div class="mini-stat">
          <span class="label">acc</span>
          <span class="val">{{ liveAccuracy() }}</span>
          <span class="pct">%</span>
        </div>
        <div class="mini-stat">
          <span class="label">combo</span>
          <span class="val">{{ combo() }}</span>
        </div>
        <div class="mini-stat">
          <span class="label">batch</span>
          <span class="val">{{ currentBatchNum() }} / {{ totalBatches() }}</span>
        </div>
      </div>

      <!-- Settings -->
      <div class="settings-group">
        <div class="wc-settings">
          <span class="setting-title">Batch Size: </span>
          <button class="setting-btn" [class.active-btn]="lessonWordCount === 15"
                  (click)="changeWordCount(15)">15</button>
          <button class="setting-btn" [class.active-btn]="lessonWordCount === 30"
                  (click)="changeWordCount(30)">30</button>
          <button class="setting-btn" [class.active-btn]="lessonWordCount === 60"
                  (click)="changeWordCount(60)">60</button>
        </div>
      </div>

      <!-- Typing Stage -->
      <div class="main-stage">
        <div class="text-container" #textContainer>
          <div class="caret" #caret [class.idle]="!isActive"></div>
          @for (char of chars(); track $index) {
            <span class="char"
                  [class.correct]="char.state === 'correct'"
                  [class.incorrect]="char.state === 'incorrect'"
                  #charEl>{{ char.char }}</span>
          }
        </div>
      </div>

      <!-- Virtual Keyboard -->
      <div class="keyboard-container">
        <div class="keyboard isolate-both">
          <!-- Row 1 -->
          <div class="key f-l-pinky" [class.active]="activeKeys['Backquote']" [class.error]="errorKeys['Backquote']">\`</div>
          <div class="key f-l-pinky" [class.active]="activeKeys['Digit1']" [class.error]="errorKeys['Digit1']">1</div>
          <div class="key f-l-ring" [class.active]="activeKeys['Digit2']" [class.error]="errorKeys['Digit2']">2</div>
          <div class="key f-l-middle" [class.active]="activeKeys['Digit3']" [class.error]="errorKeys['Digit3']">3</div>
          <div class="key f-l-index" [class.active]="activeKeys['Digit4']" [class.error]="errorKeys['Digit4']">4</div>
          <div class="key f-l-index" [class.active]="activeKeys['Digit5']" [class.error]="errorKeys['Digit5']">5</div>
          <div class="key f-r-index" [class.active]="activeKeys['Digit6']" [class.error]="errorKeys['Digit6']">6</div>
          <div class="key f-r-index" [class.active]="activeKeys['Digit7']" [class.error]="errorKeys['Digit7']">7</div>
          <div class="key f-r-middle" [class.active]="activeKeys['Digit8']" [class.error]="errorKeys['Digit8']">8</div>
          <div class="key f-r-ring" [class.active]="activeKeys['Digit9']" [class.error]="errorKeys['Digit9']">9</div>
          <div class="key f-r-pinky" [class.active]="activeKeys['Digit0']" [class.error]="errorKeys['Digit0']">0</div>
          <div class="key f-r-pinky" [class.active]="activeKeys['Minus']" [class.error]="errorKeys['Minus']">-</div>
          <div class="key f-r-pinky" [class.active]="activeKeys['Equal']" [class.error]="errorKeys['Equal']">=</div>
          <div class="key wide f-r-pinky" [class.active]="activeKeys['Backspace']">&#x232B;</div>
          <!-- Row 2 -->
          <div class="key wide f-l-pinky">&#x21E5;</div>
          <div class="key left-hand f-l-pinky" [class.active]="activeKeys['KeyQ']" [class.error]="errorKeys['KeyQ']">Q</div>
          <div class="key left-hand f-l-ring" [class.active]="activeKeys['KeyW']" [class.error]="errorKeys['KeyW']">W</div>
          <div class="key left-hand f-l-middle" [class.active]="activeKeys['KeyE']" [class.error]="errorKeys['KeyE']">E</div>
          <div class="key left-hand f-l-index" [class.active]="activeKeys['KeyR']" [class.error]="errorKeys['KeyR']">R</div>
          <div class="key left-hand f-l-index" [class.active]="activeKeys['KeyT']" [class.error]="errorKeys['KeyT']">T</div>
          <div class="key right-hand f-r-index" [class.active]="activeKeys['KeyY']" [class.error]="errorKeys['KeyY']">Y</div>
          <div class="key right-hand f-r-index" [class.active]="activeKeys['KeyU']" [class.error]="errorKeys['KeyU']">U</div>
          <div class="key right-hand f-r-middle" [class.active]="activeKeys['KeyI']" [class.error]="errorKeys['KeyI']">I</div>
          <div class="key right-hand f-r-ring" [class.active]="activeKeys['KeyO']" [class.error]="errorKeys['KeyO']">O</div>
          <div class="key right-hand f-r-pinky" [class.active]="activeKeys['KeyP']" [class.error]="errorKeys['KeyP']">P</div>
          <div class="key right-hand f-r-pinky" [class.active]="activeKeys['BracketLeft']">[</div>
          <div class="key right-hand f-r-pinky" [class.active]="activeKeys['BracketRight']">]</div>
          <div class="key wide f-r-pinky" [class.active]="activeKeys['Backslash']">\\</div>
          <!-- Row 3 -->
          <div class="key extra-wide f-l-pinky">Caps</div>
          <div class="key left-hand f-l-pinky" [class.active]="activeKeys['KeyA']" [class.error]="errorKeys['KeyA']">A</div>
          <div class="key left-hand f-l-ring" [class.active]="activeKeys['KeyS']" [class.error]="errorKeys['KeyS']">S</div>
          <div class="key left-hand f-l-middle" [class.active]="activeKeys['KeyD']" [class.error]="errorKeys['KeyD']">D</div>
          <div class="key left-hand f-l-index" [class.active]="activeKeys['KeyF']" [class.error]="errorKeys['KeyF']">F</div>
          <div class="key left-hand f-l-index" [class.active]="activeKeys['KeyG']" [class.error]="errorKeys['KeyG']">G</div>
          <div class="key right-hand f-r-index" [class.active]="activeKeys['KeyH']" [class.error]="errorKeys['KeyH']">H</div>
          <div class="key right-hand f-r-index" [class.active]="activeKeys['KeyJ']" [class.error]="errorKeys['KeyJ']">J</div>
          <div class="key right-hand f-r-middle" [class.active]="activeKeys['KeyK']" [class.error]="errorKeys['KeyK']">K</div>
          <div class="key right-hand f-r-ring" [class.active]="activeKeys['KeyL']" [class.error]="errorKeys['KeyL']">L</div>
          <div class="key right-hand f-r-pinky" [class.active]="activeKeys['Semicolon']">;</div>
          <div class="key right-hand f-r-pinky" [class.active]="activeKeys['Quote']">'</div>
          <div class="key extra-wide f-r-pinky" [class.active]="activeKeys['Enter']">&#x23CE;</div>
          <!-- Row 4 -->
          <div class="key super-wide f-l-pinky">&#x21E7;</div>
          <div class="key left-hand f-l-pinky" [class.active]="activeKeys['KeyZ']" [class.error]="errorKeys['KeyZ']">Z</div>
          <div class="key left-hand f-l-ring" [class.active]="activeKeys['KeyX']" [class.error]="errorKeys['KeyX']">X</div>
          <div class="key left-hand f-l-middle" [class.active]="activeKeys['KeyC']" [class.error]="errorKeys['KeyC']">C</div>
          <div class="key left-hand f-l-index" [class.active]="activeKeys['KeyV']" [class.error]="errorKeys['KeyV']">V</div>
          <div class="key left-hand f-l-index" [class.active]="activeKeys['KeyB']" [class.error]="errorKeys['KeyB']">B</div>
          <div class="key right-hand f-r-index" [class.active]="activeKeys['KeyN']" [class.error]="errorKeys['KeyN']">N</div>
          <div class="key right-hand f-r-index" [class.active]="activeKeys['KeyM']" [class.error]="errorKeys['KeyM']">M</div>
          <div class="key right-hand f-r-middle" [class.active]="activeKeys['Comma']">,</div>
          <div class="key right-hand f-r-ring" [class.active]="activeKeys['Period']">.</div>
          <div class="key right-hand f-r-pinky" [class.active]="activeKeys['Slash']">/</div>
          <div class="key super-wide f-r-pinky">&#x21E7;</div>
          <!-- Row 5 -->
          <div class="key space-bar f-thumb" [class.active]="activeKeys['Space']">Space</div>
        </div>
      </div>
    </div>
  `,
    styleUrls: ['./standard-typing.component.scss'],
})
export class StandardTypingComponent implements OnInit, OnDestroy, AfterViewInit {
    @Input({ required: true }) level!: Level;
    @Output() completed = new EventEmitter<{ wpm: number; accuracy: number }>();

    @ViewChild('textContainer') textContainerRef!: ElementRef<HTMLDivElement>;
    @ViewChild('caret') caretRef!: ElementRef<HTMLDivElement>;

    chars = signal<{ char: string; state: 'pending' | 'correct' | 'incorrect' }[]>([]);
    liveWpm = signal<number>(0);
    liveAccuracy = signal<number>(100);
    combo = signal<number>(0);
    currentBatchNum = signal<number>(1);
    totalBatches = signal<number>(1);

    isActive = false;
    lessonWordCount = 15;

    activeKeys: Record<string, boolean> = {};
    errorKeys: Record<string, boolean> = {};

    private fullWords: string[] = [];
    private currentBatchIndex = 0; // index of which batch we are on
    private currentIndex = 0; // index within the CURRENT batch
    private startTime: number | null = null;
    private absTotalTyped = 0;
    private absErrors = 0;
    private wpmInterval: ReturnType<typeof setInterval> | null = null;
    private charElements: HTMLSpanElement[] = [];

    ngOnInit(): void {
        this.initLessonSource();
    }

    ngAfterViewInit(): void {
        setTimeout(() => {
            this.collectCharElements();
            this.updateCaretPosition();
        });
    }

    ngOnDestroy(): void {
        if (this.wpmInterval) clearInterval(this.wpmInterval);
    }

    private initLessonSource(): void {
        // Build the total word bank
        const textToUse = this.level.text || generateLesson('both', 500);
        this.fullWords = textToUse.trim().split(/\s+/);
        
        this.absTotalTyped = 0;
        this.absErrors = 0;
        this.startTime = null;
        this.isActive = false;
        this.combo.set(0);
        this.liveWpm.set(0);
        this.liveAccuracy.set(100);
        
        this.loadBatch(0);
    }

    private loadBatch(batchIdx: number): void {
        this.currentBatchIndex = batchIdx;
        this.currentIndex = 0;
        this.currentBatchNum.set(batchIdx + 1);
        this.totalBatches.set(Math.ceil(this.fullWords.length / this.lessonWordCount));

        const start = batchIdx * this.lessonWordCount;
        const end = start + this.lessonWordCount;
        const batchWords = this.fullWords.slice(start, end);
        
        // If we are out of words, game is complete!
        if (batchWords.length === 0) {
            this.finish();
            return;
        }

        const batchText = batchWords.join(' ');
        this.chars.set(
            batchText.split('').map((c) => ({ char: c, state: 'pending' as const }))
        );

        setTimeout(() => {
            this.collectCharElements();
            this.updateCaretPosition();
        });
    }

    changeWordCount(count: number): void {
        this.lessonWordCount = count;
        // Resest progress completely on batch size change
        this.initLessonSource();
    }

    private collectCharElements(): void {
        if (!this.textContainerRef) return;
        const container = this.textContainerRef.nativeElement;
        this.charElements = Array.from(container.querySelectorAll('.char'));
    }

    focus(): void {
        (document.activeElement as HTMLElement)?.blur();
    }

    @HostListener('window:keydown', ['$event'])
    onKeyDown(event: KeyboardEvent): void {
        if (event.key === 'Tab' || event.key === 'Enter') {
            event.preventDefault();
            return;
        }
        if (event.key === ' ') event.preventDefault();

        this.activeKeys[event.code] = true;

        if (event.key === 'Backspace') {
            if (this.currentIndex > 0) {
                this.currentIndex--;
                this.chars.update((arr) => {
                    const copy = [...arr];
                    copy[this.currentIndex] = { ...copy[this.currentIndex], state: 'pending' };
                    return copy;
                });
                this.combo.set(0);
                this.updateCaretPosition();
                this.updateMetrics();
            }
            return;
        }

        if (event.key.length !== 1) return;

        if (!this.isActive) {
            this.isActive = true;
            this.startTime = performance.now();
            this.wpmInterval = setInterval(() => this.updateMetrics(), 200);
        }

        const currentBatchMax = this.chars().length;
        if (this.currentIndex >= currentBatchMax) return;

        const expected = this.chars()[this.currentIndex].char;
        const state = event.key === expected ? 'correct' : 'incorrect';

        if (state === 'incorrect') {
            this.absErrors++;
            this.combo.set(0);
            this.errorKeys[event.code] = true;
            this.triggerShake();
        } else {
            this.combo.update(c => c + 1);
        }

        this.absTotalTyped++;

        this.chars.update((arr) => {
            const copy = [...arr];
            copy[this.currentIndex] = { ...copy[this.currentIndex], state };
            return copy;
        });

        this.currentIndex++;
        this.updateCaretPosition();
        this.updateMetrics();

        // Check if we finished the batch
        if (this.currentIndex === currentBatchMax) {
            // Wait slightly before loading next batch to show completion 
            setTimeout(() => {
                this.loadBatch(this.currentBatchIndex + 1);
            }, 150);
        }
    }

    @HostListener('window:keyup', ['$event'])
    onKeyUp(event: KeyboardEvent): void {
        this.activeKeys[event.code] = false;
        setTimeout(() => {
            this.errorKeys[event.code] = false;
        }, 100);
    }

    private triggerShake(): void {
        if (!this.textContainerRef) return;
        const el = this.textContainerRef.nativeElement;
        el.classList.remove('shake-animation');
        void el.offsetWidth;
        el.classList.add('shake-animation');
    }

    private updateCaretPosition(): void {
        if (!this.caretRef || this.charElements.length === 0) return;
        const caret = this.caretRef.nativeElement;

        if (this.currentIndex < this.charElements.length) {
            const target = this.charElements[this.currentIndex];
            caret.style.transform = `translate(${target.offsetLeft}px, ${target.offsetTop}px)`;
        } else if (this.charElements.length > 0) {
            const last = this.charElements[this.charElements.length - 1];
            caret.style.transform = `translate(${last.offsetLeft + last.offsetWidth}px, ${last.offsetTop}px)`;
        }
    }

    private updateMetrics(): void {
        if (!this.startTime) return;
        const minutes = (performance.now() - this.startTime) / 60000;
        // Total valid words calculated by absolute correct chars / 5
        const validChars = Math.max(0, this.absTotalTyped - this.absErrors);
        const words = validChars / 5;
        this.liveWpm.set(minutes > 0 ? Math.round(words / minutes) : 0);
        this.liveAccuracy.set(
            this.absTotalTyped > 0
                ? Math.round(((this.absTotalTyped - this.absErrors) / this.absTotalTyped) * 100)
                : 100
        );
    }

    private finish(): void {
        this.isActive = false;
        if (this.wpmInterval) clearInterval(this.wpmInterval);
        this.updateMetrics();
        this.completed.emit({
            wpm: this.liveWpm(),
            accuracy: this.liveAccuracy(),
        });
    }
}
