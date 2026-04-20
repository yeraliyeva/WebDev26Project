import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../core/services/auth.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';
import { Avatar } from '../../../core/models';
import { normalizeStorageUrl } from '../../../core/utils/storage-url';

@Component({
    selector: 'app-register',
    standalone: true,
    imports: [FormsModule, CommonModule, RouterLink],
    templateUrl: './register.component.html',
    styleUrls: ['./register.component.scss'],
})
export class RegisterComponent implements OnInit {
    username = '';
    email = '';
    password = '';
    passwordConfirm = '';
    selectedAvatarId: string | null = null;

    avatars = signal<Avatar[]>([]);
    error = signal<string>('');
    loading = signal<boolean>(false);

    constructor(
        private auth: AuthService,
        private http: HttpClient,
        private router: Router
    ) { }

    ngOnInit(): void {
        this.http
            .get<Avatar[]>(`${environment.apiBase}/auth/avatars`)
            .subscribe({
                next: (data) => this.avatars.set(
                    data.map((a) => ({ ...a, image_url: normalizeStorageUrl(a.image_url) }))
                ),
                error: (err) => console.error('Failed to fetch avatars:', err)
            });
    }

    selectAvatar(id: string): void {
        this.selectedAvatarId = id;
    }

    validateEmail(email: string): boolean {
        const re = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
        return re.test(email);
    }

    onSubmit(): void {
        // Front-end Validations
        if (!this.username.trim()) {
            this.error.set('Username is required.');
            return;
        }

        if (!this.validateEmail(this.email)) {
            this.error.set('Please enter a valid email address.');
            return;
        }

        if (this.password.length < 8) {
            this.error.set('Password must be at least 8 characters.');
            return;
        }

        if (this.password !== this.passwordConfirm) {
            this.error.set('Passwords do not match!');
            return;
        }

        this.loading.set(true);
        this.error.set('');

        this.auth
            .register({
                username: this.username,
                email: this.email,
                password: this.password,
                profile_image: this.selectedAvatarId,
            })
            .subscribe({
                next: () => {
                    // Auto-login after successful registration to avoid UX dead-ends.
                    this.auth.login(this.username, this.password).subscribe({
                        next: () => this.router.navigate(['/dashboard']),
                        error: () => this.router.navigate(['/login']),
                    });
                },
                error: (err) => {
                    let msg = 'Registration failed. Please try again.';
                    if (err.error) {
                         // Parse DRF validation dict
                         if (typeof err.error === 'object') {
                             const errors = [];
                             for (const [key, val] of Object.entries(err.error)) {
                                 if (Array.isArray(val)) {
                                     errors.push(`${key}: ${val[0]}`);
                                 } else {
                                     errors.push(`${key}: ${val}`);
                                 }
                             }
                             msg = errors.join(' | ');
                         } else {
                             msg = err.error.toString();
                         }
                    }
                    this.error.set(msg);
                    this.loading.set(false);
                },
            });
    }
}
