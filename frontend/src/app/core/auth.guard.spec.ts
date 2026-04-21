import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { authGuard } from './auth.guard';

describe('authGuard', () => {
  it('allows authenticated users and redirects anonymous ones', () => {
    const createUrlTree = vi.fn((commands: string[]) => ({ commands }));

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { isAuthenticated: () => true } },
        { provide: Router, useValue: { createUrlTree } }
      ]
    });

    const allowed = TestBed.runInInjectionContext(() => authGuard({} as never, {} as never));
    expect(allowed).toBe(true);

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { isAuthenticated: () => false } },
        { provide: Router, useValue: { createUrlTree } }
      ]
    });

    const denied = TestBed.runInInjectionContext(() => authGuard({} as never, {} as never));
    expect(denied).toEqual({ commands: ['/auth'] });
    expect(createUrlTree).toHaveBeenCalledWith(['/auth']);
  });
});
