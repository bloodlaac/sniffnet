import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  it('adds bearer token and logs out on 401 responses', () => {
    const auth = {
      token: () => 'jwt-token',
      isAuthenticated: () => true,
      logout: vi.fn()
    };
    const router = {
      navigate: vi.fn().mockResolvedValue(true)
    };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: router }
      ]
    });

    const http = TestBed.inject(HttpClient);
    const httpMock = TestBed.inject(HttpTestingController);

    http.get('/api/auth/me').subscribe({ error: () => undefined });

    const request = httpMock.expectOne('/api/auth/me');
    expect(request.request.headers.get('Authorization')).toBe('Bearer jwt-token');
    request.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(auth.logout).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/auth']);
    httpMock.verify();
  });
});
