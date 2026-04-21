import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { AuthService } from '../core/auth.service';
import { AuthPageComponent } from './auth-page.component';

describe('AuthPageComponent', () => {
  it('submits login form and navigates to dashboard on success', () => {
    const auth = {
      isAuthenticated: () => false,
      login: vi.fn(() =>
        of({
          token: 'token',
          user: { id: 2, username: 'demo', email: 'demo@sniffnet.local', role: 'ROLE_USER' }
        })
      ),
      register: vi.fn()
    };
    const router = { navigate: vi.fn().mockResolvedValue(true) };

    TestBed.configureTestingModule({
      imports: [AuthPageComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: router }
      ]
    });

    const fixture = TestBed.createComponent(AuthPageComponent);
    const component = fixture.componentInstance;
    component.loginForm.setValue({ username: 'demo', password: 'demo123' });

    component.submitLogin();

    expect(auth.login).toHaveBeenCalledWith({ username: 'demo', password: 'demo123' });
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.error()).toBe('');
  });

  it('shows formatted api error when registration fails', () => {
    const auth = {
      isAuthenticated: () => false,
      login: vi.fn(),
      register: vi.fn(() =>
        throwError(() => ({
          error: {
            message: 'Validation failed',
            validationErrors: { email: 'already exists' }
          }
        }))
      )
    };

    TestBed.configureTestingModule({
      imports: [AuthPageComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: { navigate: vi.fn().mockResolvedValue(true) } }
      ]
    });

    const fixture = TestBed.createComponent(AuthPageComponent);
    const component = fixture.componentInstance;
    component.mode.set('register');
    component.registerForm.setValue({
      username: 'student',
      email: 'student@sniffnet.local',
      password: 'secret123'
    });

    component.submitRegister();
    fixture.detectChanges();

    expect(component.error()).toBe('email: already exists');
    expect(fixture.nativeElement.querySelector('.error-banner')?.textContent).toContain('email: already exists');
  });
});
