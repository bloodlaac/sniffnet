import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { AuthService } from '../core/auth.service';
import { ShellComponent } from './shell.component';

@Component({ standalone: true, template: '' })
class DummyComponent {}

describe('ShellComponent', () => {
  it('loads current user, exposes admin navigation and logs out', () => {
    const auth = {
      currentUser: () => ({
        id: 1,
        username: 'admin',
        email: 'admin@sniffnet.local',
        role: 'ROLE_ADMIN' as const
      }),
      isAdmin: () => true,
      isAuthenticated: () => true,
      loadCurrentUser: vi.fn(() => of(null)),
      logout: vi.fn()
    };

    TestBed.configureTestingModule({
      imports: [ShellComponent],
      providers: [
        provideRouter([
          { path: 'dashboard', component: DummyComponent },
          { path: 'experiments', component: DummyComponent },
          { path: 'classification', component: DummyComponent },
          { path: 'history', component: DummyComponent },
          { path: 'profile', component: DummyComponent },
          { path: 'admin/users', component: DummyComponent },
          { path: 'auth', component: DummyComponent }
        ]),
        { provide: AuthService, useValue: auth }
      ]
    });

    const fixture = TestBed.createComponent(ShellComponent);
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    fixture.detectChanges();

    expect(auth.loadCurrentUser).toHaveBeenCalled();
    expect(component.navigation().some((item) => item.link === '/admin/users')).toBe(true);

    component.logout();

    expect(auth.logout).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/auth']);
  });
});
