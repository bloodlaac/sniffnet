import { CommonModule, DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { User } from '../core/api.models';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-admin-users-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, DatePipe],
  template: `
    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    <section class="page-grid">
      <article class="card">
        <div class="section-head">
          <div>
            <p class="eyebrow">Admin</p>
            <h2>Пользователи</h2>
          </div>

          <label>
            Поиск
            <input type="text" [value]="search()" (input)="search.set($any($event.target).value); load()" placeholder="username" />
          </label>
        </div>

        <div class="user-list">
          @for (user of users(); track user.id) {
            <button type="button" class="user-row" [class.active]="selectedUser()?.id === user.id" (click)="selectUser(user)">
              <div>
                <strong>{{ user.username }}</strong>
                <p>{{ user.email }}</p>
              </div>
              <div class="user-meta">
                <span>{{ user.role }}</span>
                <span>{{ user.createdAt | date: 'dd.MM.yyyy' }}</span>
              </div>
            </button>
          }
        </div>
      </article>

      <article class="card">
        <p class="eyebrow">Editor</p>
        <h2>Изменение учетной записи</h2>

        @if (selectedUser()) {
          <form class="form-grid" [formGroup]="form" (ngSubmit)="save()">
            <label>
              Username
              <input type="text" formControlName="username" />
            </label>

            <label>
              Email
              <input type="email" formControlName="email" />
            </label>

            <label>
              Роль
              <select formControlName="role">
                <option value="ROLE_USER">ROLE_USER</option>
                <option value="ROLE_ADMIN">ROLE_ADMIN</option>
              </select>
            </label>

            <button type="submit" class="primary-button">Сохранить</button>
            <button type="button" class="ghost-button" (click)="remove()">Удалить</button>
          </form>
        } @else {
          <p class="empty-state">Выберите пользователя из списка слева.</p>
        }
      </article>
    </section>
  `,
  styles: `
    .page-grid {
      display: grid;
      grid-template-columns: 1fr 0.9fr;
      gap: 1rem;
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: end;
      margin-bottom: 1rem;
    }

    .section-head h2 {
      margin: 0.25rem 0 0;
    }

    .user-list {
      display: grid;
      gap: 0.75rem;
    }

    .user-row {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
      width: 100%;
      text-align: left;
      padding: 1rem;
      border-radius: 1rem;
      border: 1px solid rgba(28, 71, 44, 0.12);
      background: var(--color-surface-tint);
    }

    .user-row.active {
      border-color: var(--color-accent);
      box-shadow: 0 0 0 3px rgba(168, 210, 47, 0.18);
    }

    .user-row p {
      margin: 0.35rem 0 0;
      color: var(--color-text-muted);
    }

    .user-meta {
      display: grid;
      justify-items: end;
      gap: 0.3rem;
      color: var(--color-text-muted);
      font-size: 0.88rem;
    }

    .empty-state {
      color: var(--color-text-muted);
      margin: 1rem 0 0;
    }

    @media (max-width: 1120px) {
      .page-grid {
        grid-template-columns: 1fr;
      }
    }
  `
})
export class AdminUsersPageComponent {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);

  readonly users = signal<User[]>([]);
  readonly selectedUser = signal<User | null>(null);
  readonly search = signal('');
  readonly error = signal('');

  readonly form = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    role: ['ROLE_USER', [Validators.required]]
  });

  constructor() {
    this.load();
  }

  selectUser(user: User): void {
    this.selectedUser.set(user);
    this.form.patchValue({
      username: user.username,
      email: user.email,
      role: user.role
    });
  }

  save(): void {
    const user = this.selectedUser();
    if (!user || this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.api.put<User>(`/users/${user.id}`, this.form.getRawValue()).subscribe({
      next: (updated) => {
        this.selectedUser.set(updated);
        this.load();
      },
      error: (err) => this.error.set(formatApiError(err))
    });
  }

  remove(): void {
    const user = this.selectedUser();
    if (!user || !confirm(`Удалить пользователя ${user.username}?`)) {
      return;
    }

    this.api.delete(`/users/${user.id}`).subscribe({
      next: () => {
        this.selectedUser.set(null);
        this.load();
      },
      error: (err) => this.error.set(formatApiError(err))
    });
  }

  load(): void {
    this.api.get<User[]>('/users', { search: this.search() || undefined }).subscribe({
      next: (response) => this.users.set(response),
      error: (err) => this.error.set(formatApiError(err))
    });
  }
}
