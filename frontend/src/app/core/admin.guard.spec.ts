import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { adminGuard } from './admin.guard';

describe('adminGuard', () => {
  it('allows admins and redirects regular users to dashboard', () => {
    const createUrlTree = vi.fn((commands: string[]) => ({ commands }));

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { isAdmin: () => true } },
        { provide: Router, useValue: { createUrlTree } }
      ]
    });

    const allowed = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(allowed).toBe(true);

    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { isAdmin: () => false } },
        { provide: Router, useValue: { createUrlTree } }
      ]
    });

    const denied = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));
    expect(denied).toEqual({ commands: ['/dashboard'] });
    expect(createUrlTree).toHaveBeenCalledWith(['/dashboard']);
  });
});
