import { CommonModule, DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { AuthService } from '../core/auth.service';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule, DatePipe],
  template: `
    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    @if (auth.currentUser(); as user) {
      <section class="profile-grid">
        <article class="card">
          <p class="eyebrow">Profile</p>
          <h2>{{ user.username }}</h2>
          <div class="info-grid">
            <div>
              <span>Username</span>
              <strong>{{ user.username }}</strong>
            </div>
            <div>
              <span>Email</span>
              <strong>{{ user.email }}</strong>
            </div>
            <div>
              <span>Роль</span>
              <strong>{{ user.role }}</strong>
            </div>
            <div>
              <span>Создан</span>
              <strong>{{ user.createdAt ? (user.createdAt | date: 'dd.MM.yyyy HH:mm') : 'Дата отсутствует' }}</strong>
            </div>
          </div>
        </article>
      </section>
    }
  `,
  styles: `
    .profile-grid {
      display: grid;
      gap: 1rem;
    }

    .card h2 {
      margin: 0.25rem 0 1rem;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.9rem;
    }

    .info-grid div {
      padding: 0.95rem;
      border-radius: 1rem;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.08);
    }

    .info-grid span {
      display: block;
      color: var(--color-text-muted);
      font-size: 0.85rem;
      margin-bottom: 0.3rem;
    }

    @media (max-width: 960px) {
      .info-grid {
        grid-template-columns: 1fr;
      }
    }
  `
})
export class ProfilePageComponent {
  readonly auth = inject(AuthService);
  readonly error = signal('');

  constructor() {
    this.auth.loadCurrentUser().subscribe({
      error: (err) => this.error.set(formatApiError(err))
    });
  }
}
