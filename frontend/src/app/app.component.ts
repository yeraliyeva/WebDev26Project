import { Component, computed } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CommonModule, FormsModule],
  template: `
    <header class="top-nav">
      <a routerLink="/dashboard" class="logo">TYPECAT</a>

      <div class="nav-links">
        <a routerLink="/leaderboard" class="nav-link">leaderboard</a>

        <select class="setting-select" (change)="onThemeChange($event)">
          <option value="default">Studio</option>
          <option value="mocha">Mocha</option>
          <option value="sakura">Sakura</option>
          <option value="light">Light</option>
          <option value="midnight">Midnight</option>
        </select>

        @if (auth.isLoggedIn()) {
          <button (click)="auth.logout()" class="btn-logout">logout</button>
        } @else {
          <a routerLink="/login" class="nav-link">login</a>
          <a routerLink="/register" class="nav-link">register</a>
        }
      </div>
    </header>

    <main class="content">
      <router-outlet />
    </main>
  `,
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  constructor(public auth: AuthService) { }

  onThemeChange(event: Event): void {
    const theme = (event.target as HTMLSelectElement).value;
    document.body.dataset['theme'] = theme;
  }
}
