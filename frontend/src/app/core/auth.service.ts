import { Injectable, computed, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';
import { ApiService } from './api.service';
import { AuthResponse, CurrentUser } from './api.models';

interface AuthSession {
  token: string;
  user: CurrentUser;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly storageKey = 'sniffnet.auth';
  private readonly sessionState = signal<AuthSession | null>(this.readStorage());

  constructor(private readonly api: ApiService) {}

  readonly session = computed(() => this.sessionState());
  readonly token = computed(() => this.sessionState()?.token ?? null);
  readonly currentUser = computed(() => this.sessionState()?.user ?? null);
  readonly isAuthenticated = computed(() => !!this.token());
  readonly isAdmin = computed(() => this.currentUser()?.role === 'ROLE_ADMIN');

  login(payload: { username: string; password: string }): Observable<AuthSession> {
    return this.api.post<AuthResponse>('/auth/login', payload).pipe(
      map((response) => this.toSession(response)),
      tap((session) => this.saveSession(session))
    );
  }

  register(payload: { username: string; email: string; password: string }): Observable<AuthSession> {
    return this.api.post<AuthResponse>('/auth/register', payload).pipe(
      map((response) => this.toSession(response)),
      tap((session) => this.saveSession(session))
    );
  }

  loadCurrentUser(): Observable<CurrentUser> {
    return this.api.get<CurrentUser>('/auth/me').pipe(
      tap((user) => {
        const session = this.sessionState();
        if (session) {
          this.saveSession({ ...session, user });
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem(this.storageKey);
    this.sessionState.set(null);
  }

  private toSession(response: AuthResponse): AuthSession {
    return {
      token: response.token,
      user: {
        id: response.userId,
        username: response.username,
        email: response.email,
        role: response.role
      }
    };
  }

  private saveSession(session: AuthSession): void {
    this.sessionState.set(session);
    localStorage.setItem(this.storageKey, JSON.stringify(session));
  }

  private readStorage(): AuthSession | null {
    const raw = localStorage.getItem(this.storageKey);
    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as AuthSession;
    } catch {
      localStorage.removeItem(this.storageKey);
      return null;
    }
  }
}
