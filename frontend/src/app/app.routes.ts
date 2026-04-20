import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
    },
    {
        path: 'login',
        loadComponent: () =>
            import('./features/auth/login/login.component').then(
                (m) => m.LoginComponent
            ),
    },
    {
        path: 'register',
        loadComponent: () =>
            import('./features/auth/register/register.component').then(
                (m) => m.RegisterComponent
            ),
    },
    {
        path: 'dashboard',
        canActivate: [authGuard],
        loadComponent: () =>
            import('./features/dashboard/dashboard.component').then(
                (m) => m.DashboardComponent
            ),
    },
    {
        path: 'leaderboard',
        loadComponent: () =>
            import('./features/leaderboard/leaderboard.component').then(
                (m) => m.LeaderboardComponent
            ),
    },
    {
        path: 'test-leaderboard',
        loadComponent: () =>
            import('./features/leaderboard/test-leaderboard.component').then(
                (m) => m.TestLeaderboardComponent
            ),
    },
    {
        path: 'play/:id',
        canActivate: [authGuard],
        loadComponent: () =>
            import('./features/game/game-play/game-play.component').then(
                (m) => m.GamePlayComponent
            ),
    },
    {
        path: '**',
        redirectTo: 'dashboard',
    },
];
