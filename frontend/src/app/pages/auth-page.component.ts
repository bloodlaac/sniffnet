import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../core/auth.service';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-auth-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="auth-layout">
      <div class="auth-copy card">
        <div class="auth-copy-inner">
          <div>
            <p class="eyebrow">SniffNet</p>
            <h1>Оценка свежести продуктов по фотографии</h1>
            <p class="lead">
              Учебное веб-приложение для курсовой работы по Java Spring и Angular.
            </p>
          </div>

          <div class="auth-points">
            <div class="auth-point">
              <strong>Работа с моделями</strong>
              <p>Просмотр доступных моделей и их метрик.</p>
            </div>
            <div class="auth-point">
              <strong>Эксперименты обучения</strong>
              <p>Создание и просмотр запусков обучения.</p>
            </div>
            <div class="auth-point">
              <strong>Инференс по фото</strong>
              <p>Загрузка изображения и получение результата классификации.</p>
            </div>
          </div>

          <div class="auth-note">
            Доступ к системе выполняется после регистрации или входа в учетную запись.
          </div>
        </div>
      </div>

      <div class="auth-panel card">
        <div class="tabs">
          <button type="button" [class.active]="mode() === 'login'" (click)="mode.set('login')">
            Вход
          </button>
          <button type="button" [class.active]="mode() === 'register'" (click)="mode.set('register')">
            Регистрация
          </button>
        </div>

        @if (error()) {
          <div class="error-banner">{{ error() }}</div>
        }

        @if (mode() === 'login') {
          <form class="form-grid" [formGroup]="loginForm" (submit)="$event.preventDefault(); submitLogin()">
            <label>
              Username
              <input type="text" formControlName="username" placeholder="demo" />
            </label>
            @if (loginForm.controls.username.invalid && loginForm.controls.username.touched) {
              <div class="field-error">Введите username.</div>
            }
            <label>
              Пароль
              <input type="password" formControlName="password" placeholder="demo123" />
            </label>
            @if (loginForm.controls.password.invalid && loginForm.controls.password.touched) {
              <div class="field-error">Введите пароль.</div>
            }
            <button type="submit" class="primary-button" [disabled]="submitting()">
              {{ submitting() ? 'Входим...' : 'Войти' }}
            </button>
          </form>
        } @else {
          <form class="form-grid" [formGroup]="registerForm" (submit)="$event.preventDefault(); submitRegister()">
            <label>
              Username
              <input type="text" formControlName="username" placeholder="student" />
            </label>
            @if (registerForm.controls.username.invalid && registerForm.controls.username.touched) {
              <div class="field-error">
                @if (registerForm.controls.username.hasError('required')) {
                  Укажите username.
                } @else if (registerForm.controls.username.hasError('minlength')) {
                  Username должен содержать минимум 3 символа.
                }
              </div>
            }
            <label>
              Email
              <input type="email" formControlName="email" placeholder="student@sniffnet.local" />
            </label>
            @if (registerForm.controls.email.invalid && registerForm.controls.email.touched) {
              <div class="field-error">
                @if (registerForm.controls.email.hasError('required')) {
                  Укажите email.
                } @else if (registerForm.controls.email.hasError('email')) {
                  Введите корректный email, например name@example.com.
                }
              </div>
            }
            <label>
              Пароль
              <input type="password" formControlName="password" placeholder="minimum 6 symbols" />
            </label>
            @if (registerForm.controls.password.invalid && registerForm.controls.password.touched) {
              <div class="field-error">
                @if (registerForm.controls.password.hasError('required')) {
                  Укажите пароль.
                } @else if (registerForm.controls.password.hasError('minlength')) {
                  Пароль должен содержать минимум 6 символов.
                }
              </div>
            }
            <button type="submit" class="primary-button" [disabled]="submitting()">
              {{ submitting() ? 'Создаем...' : 'Создать аккаунт' }}
            </button>
          </form>
        }

        <div class="hint">
          <strong>Тестовые аккаунты:</strong> admin / admin123, demo / demo123
        </div>
      </div>
    </section>
  `,
  styles: `
    :host {
      display: block;
      min-height: 100dvh;
    }

    .auth-layout {
      min-height: 100dvh;
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 1.5rem;
      padding: 1.5rem;
      align-items: stretch;
    }

    .auth-copy,
    .auth-panel {
      padding: 2rem;
      min-height: 36rem;
    }

    .auth-copy {
      background: var(--color-sidebar);
      color: var(--color-text-strong);
      display: flex;
    }

    .auth-copy-inner {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 2rem;
      width: 100%;
    }

    .auth-copy h1 {
      font-size: clamp(2.4rem, 4.5vw, 3.6rem);
      margin: 0.5rem 0 1rem;
      max-width: 12ch;
      color: var(--color-text-strong);
      line-height: 1.08;
    }

    .lead {
      max-width: 28rem;
      color: var(--color-text-soft);
      font-size: 1.08rem;
      line-height: 1.6;
      margin: 0;
    }

    .auth-points {
      display: grid;
      gap: 0.85rem;
    }

    .auth-point {
      padding: 1rem 1.1rem;
      border-radius: 0.8rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .auth-point strong {
      display: block;
      margin-bottom: 0.35rem;
      color: var(--color-text-strong);
      font-size: 1rem;
    }

    .auth-point p,
    .auth-note {
      margin: 0;
      color: var(--color-text-soft);
      line-height: 1.5;
    }

    .auth-note {
      padding-top: 1rem;
      border-top: 1px solid rgba(255, 255, 255, 0.12);
      font-size: 0.95rem;
      max-width: 28rem;
    }

    .auth-panel {
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 1.2rem;
    }

    .tabs {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      background: var(--color-surface-tint);
      padding: 0.3rem;
      border-radius: 0.8rem;
    }

    .tabs button {
      border: 0;
      background: transparent;
      padding: 0.85rem 1rem;
      border-radius: 0.6rem;
      color: var(--color-text-muted);
    }

    .tabs button.active {
      background: var(--color-accent-strong);
      color: var(--color-text-strong);
    }

    .hint {
      margin-top: 0.5rem;
      color: var(--color-text-muted);
      font-size: 0.95rem;
    }

    .field-error {
      margin-top: -0.5rem;
      color: var(--color-danger-text);
      font-size: 0.9rem;
    }

    @media (max-width: 960px) {
      .auth-layout {
        grid-template-columns: 1fr;
      }

      .auth-copy,
      .auth-panel {
        min-height: auto;
      }

      .auth-copy h1 {
        max-width: none;
      }
    }
  `
})
export class AuthPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly mode = signal<'login' | 'register'>('login');
  readonly submitting = signal(false);
  readonly error = signal('');

  readonly loginForm = this.fb.nonNullable.group({
    username: ['demo', [Validators.required]],
    password: ['demo123', [Validators.required]]
  });

  readonly registerForm = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

  constructor() {
    if (this.auth.isAuthenticated()) {
      void this.router.navigate(['/dashboard']);
    }
  }

  submitLogin(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.error.set('');
    this.submitting.set(true);
    this.auth.login(this.loginForm.getRawValue()).subscribe({
      next: () => {
        this.submitting.set(false);
        void this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(formatApiError(err));
      }
    });
  }

  submitRegister(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.error.set('');
    this.submitting.set(true);
    this.auth.register(this.registerForm.getRawValue()).subscribe({
      next: () => {
        this.submitting.set(false);
        void this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(formatApiError(err));
      }
    });
  }
}
