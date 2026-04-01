import { Routes } from '@angular/router';
import { adminGuard } from './core/admin.guard';
import { authGuard } from './core/auth.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadComponent: () =>
      import('./pages/auth-page.component').then((m) => m.AuthPageComponent)
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./layout/shell.component').then((m) => m.ShellComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/dashboard-page.component').then((m) => m.DashboardPageComponent)
      },
      {
        path: 'experiments',
        loadComponent: () =>
          import('./pages/experiments-page.component').then((m) => m.ExperimentsPageComponent)
      },
      {
        path: 'experiments/:id',
        loadComponent: () =>
          import('./pages/experiment-detail-page.component').then((m) => m.ExperimentDetailPageComponent)
      },
      {
        path: 'classification',
        loadComponent: () =>
          import('./pages/classification-page.component').then((m) => m.ClassificationPageComponent)
      },
      {
        path: 'history',
        loadComponent: () =>
          import('./pages/history-page.component').then((m) => m.HistoryPageComponent)
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./pages/profile-page.component').then((m) => m.ProfilePageComponent)
      },
      {
        path: 'admin/users',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./pages/admin-users-page.component').then((m) => m.AdminUsersPageComponent)
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
