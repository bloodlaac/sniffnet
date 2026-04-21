import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.resetTestingModule();
  });

  it('stores session after login and exposes computed state', () => {
    TestBed.configureTestingModule({
      providers: [ApiService, AuthService, provideHttpClient(), provideHttpClientTesting()]
    });

    const service = TestBed.inject(AuthService);
    const httpMock = TestBed.inject(HttpTestingController);

    service.login({ username: 'demo', password: 'demo123' }).subscribe();

    const request = httpMock.expectOne('/api/auth/login');
    request.flush({
      token: 'token-1',
      userId: 2,
      username: 'demo',
      email: 'demo@sniffnet.local',
      role: 'ROLE_USER'
    });

    expect(service.isAuthenticated()).toBe(true);
    expect(service.currentUser()?.username).toBe('demo');
    expect(localStorage.getItem('sniffnet.auth')).toContain('"token":"token-1"');
    httpMock.verify();
  });

  it('drops broken persisted state and clears session on logout', () => {
    localStorage.setItem('sniffnet.auth', '{broken');
    TestBed.configureTestingModule({
      providers: [ApiService, AuthService, provideHttpClient(), provideHttpClientTesting()]
    });

    const service = TestBed.inject(AuthService);

    expect(service.session()).toBeNull();
    expect(localStorage.getItem('sniffnet.auth')).toBeNull();

    localStorage.setItem(
      'sniffnet.auth',
      JSON.stringify({
        token: 'token-2',
        user: { id: 1, username: 'admin', email: 'admin@sniffnet.local', role: 'ROLE_ADMIN' }
      })
    );
    service.logout();

    expect(service.isAuthenticated()).toBe(false);
    expect(localStorage.getItem('sniffnet.auth')).toBeNull();
  });
});
