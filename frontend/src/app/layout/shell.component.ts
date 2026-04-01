import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { catchError, of } from 'rxjs';
import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  template: `
    <div class="shell">
      <aside class="sidebar">
        <div>
          <a class="brand" routerLink="/dashboard">
            <span class="brand-badge">SN</span>
            <div>
              <strong>SniffNet</strong>
              <p>Система оценки свежести продуктов</p>
            </div>
          </a>

          <nav class="nav">
            @for (item of navigation(); track item.link) {
              <a
                [routerLink]="item.link"
                routerLinkActive="active"
                class="nav-link"
              >
                <span>{{ item.label }}</span>
              </a>
            }
          </nav>
        </div>

        <div class="profile-card">
          <p class="profile-label">Пользователь</p>
          <a class="profile-link" routerLink="/profile">
            <strong>{{ auth.currentUser()?.username }}</strong>
          </a>
          <p>{{ auth.currentUser()?.email }}</p>
          <span class="role-chip">{{ auth.currentUser()?.role }}</span>
          <button type="button" class="ghost-button" (click)="logout()">Выйти</button>
        </div>
      </aside>

      <main class="content">
        <header class="topbar">
          <div>
            <h1>Оценка свежести продуктов по фото</h1>
          </div>
        </header>

        <router-outlet />
      </main>
    </div>
  `,
  styles: `
    :host {
      display: block;
      min-height: 100dvh;
    }

    .shell {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100dvh;
    }

    .sidebar {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 2rem;
      padding: 1.5rem;
      background: var(--color-sidebar);
      border-right: 1px solid var(--color-sidebar-border);
      position: sticky;
      top: 0;
      height: 100dvh;
      color: var(--color-text-strong);
    }

    .brand {
      display: flex;
      gap: 1rem;
      align-items: center;
      color: var(--color-text-strong);
      text-decoration: none;
      margin-bottom: 2rem;
    }

    .brand strong {
      font-size: 1.15rem;
      display: block;
    }

    .brand p,
    .profile-card p {
      margin: 0.2rem 0 0;
      color: var(--color-text-soft);
      font-size: 0.92rem;
    }

    .brand-badge {
      display: grid;
      flex: 0 0 3rem;
      place-items: center;
      width: 3rem;
      min-width: 3rem;
      height: 3rem;
      min-height: 3rem;
      aspect-ratio: 1 / 1;
      border-radius: 0.8rem;
      background: var(--color-highlight);
      color: var(--color-sidebar);
      font-weight: 700;
    }

    .nav {
      display: grid;
      gap: 0.5rem;
    }

    .nav-link {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      padding: 0.9rem 1rem;
      border-radius: 0.8rem;
      color: var(--color-text-soft);
      text-decoration: none;
      transition: background-color 160ms ease, color 160ms ease;
    }

    .nav-link:hover,
    .nav-link.active {
      background: var(--color-sidebar-hover);
      color: var(--color-text-strong);
    }

    .profile-card {
      padding: 1rem;
      border-radius: 0.8rem;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--color-sidebar-border);
    }

    .profile-card strong {
      color: var(--color-text-strong);
    }

    .profile-link {
      color: var(--color-text-strong);
      text-decoration: none;
    }

    .profile-link:hover {
      text-decoration: underline;
    }

    .profile-label {
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.75rem;
      margin-bottom: 0.5rem;
    }

    .role-chip {
      display: inline-flex;
      margin-top: 0.9rem;
      padding: 0.35rem 0.65rem;
      border-radius: 0.8rem;
      background: rgba(255, 255, 255, 0.08);
      color: var(--color-text-strong);
      font-size: 0.82rem;
    }

    .ghost-button {
      width: 100%;
      margin-top: 1rem;
      color: var(--color-text-strong);
      background: rgba(216, 244, 208, 0.12);
      border: 1px solid var(--color-sidebar-border);
    }

    .content {
      padding: 1.75rem;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 1rem;
      margin-bottom: 1.75rem;
    }

    .topbar h1 {
      margin: 0.2rem 0 0;
      font-size: clamp(1.8rem, 3vw, 2.6rem);
    }

    .eyebrow {
      margin: 0;
      color: var(--color-accent);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
    }

    .topbar-note {
      max-width: 24rem;
      margin: 0;
      color: var(--color-text-muted);
    }

    @media (max-width: 980px) {
      .shell {
        grid-template-columns: 1fr;
      }

      .sidebar {
        position: static;
        height: auto;
      }

      .topbar {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  `
})
export class ShellComponent {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly navigation = computed(() => {
    const items = [
      { label: 'Обзор', link: '/dashboard' },
      { label: 'Эксперименты', link: '/experiments' },
      { label: 'Классификация', link: '/classification' },
      { label: 'История', link: '/history' }
    ];

    if (this.auth.isAdmin()) {
      items.push({ label: 'Пользователи', link: '/admin/users' });
    }

    return items;
  });

  constructor() {
    if (this.auth.isAuthenticated()) {
      this.auth.loadCurrentUser().pipe(catchError(() => of(null))).subscribe();
    }
  }

  logout(): void {
    this.auth.logout();
    void this.router.navigate(['/auth']);
  }
}
