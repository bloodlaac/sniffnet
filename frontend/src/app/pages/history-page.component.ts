import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnDestroy, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { catchError, forkJoin, map, of } from 'rxjs';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Classification, User } from '../core/api.models';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-history-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, DatePipe, DecimalPipe],
  template: `
    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    <section class="card">
      <div class="section-head">
        <div>
          <p class="eyebrow">Classification log</p>
          <h2>История классификаций</h2>
        </div>

        <form class="history-filter" [formGroup]="filterForm" (ngSubmit)="load()">
          @if (auth.isAdmin()) {
            <label>
              Пользователь
              <select formControlName="userId">
                <option value="">Все</option>
                @for (user of users(); track user.id) {
                  <option [value]="user.id">{{ user.username }}</option>
                }
              </select>
            </label>
          }
          <label>
            От
            <input type="date" formControlName="from" />
          </label>
          <label>
            До
            <input type="date" formControlName="to" />
          </label>
          <button type="submit" class="ghost-button">Применить</button>
        </form>
      </div>

      <div class="history-grid">
        @for (item of history(); track item.id) {
          <article class="history-card">
            @if (imageUrl(item.imageId); as src) {
              <img [src]="src" alt="history image" />
            }
            <div class="history-body">
              <div class="history-head">
                <strong>{{ item.predictedClass || 'Ожидание' }}</strong>
                <span>{{ item.status }}</span>
              </div>
              <p>{{ item.modelName }}</p>
              <p>{{ item.createdAt | date: 'dd.MM.yyyy HH:mm' }}</p>
              <div class="confidence-line">
                <span>Уверенность</span>
                <strong>
                  @if (item.confidence !== null && item.confidence !== undefined) {
                    {{ item.confidence | number: '1.2-2' }}
                  } @else {
                    значение отсутствует
                  }
                </strong>
              </div>
            </div>
          </article>
        }
      </div>
    </section>
  `,
  styles: `
    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: end;
      margin-bottom: 1rem;
    }

    .section-head h2 {
      margin: 0.25rem 0 0;
    }

    .history-filter {
      display: flex;
      gap: 0.8rem;
      align-items: end;
      flex-wrap: wrap;
    }

    .history-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1rem;
    }

    .history-card {
      overflow: hidden;
      border-radius: 1.1rem;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.1);
    }

    .history-card img {
      width: 100%;
      height: 13rem;
      object-fit: cover;
      display: block;
    }

    .history-body {
      padding: 1rem;
    }

    .history-head,
    .confidence-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .history-body p {
      margin: 0.45rem 0;
      color: var(--color-text-muted);
    }

    @media (max-width: 1120px) {
      .history-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 720px) {
      .section-head {
        align-items: stretch;
      }

      .history-grid {
        grid-template-columns: 1fr;
      }
    }
  `
})
export class HistoryPageComponent implements OnDestroy {
  readonly api = inject(ApiService);
  readonly auth = inject(AuthService);
  private readonly fb = inject(FormBuilder);

  readonly history = signal<Classification[]>([]);
  readonly users = signal<User[]>([]);
  readonly imageUrls = signal<Record<number, string>>({});
  readonly error = signal('');

  readonly filterForm = this.fb.nonNullable.group({
    userId: [''],
    from: [''],
    to: ['']
  });

  constructor() {
    if (this.auth.isAdmin()) {
      this.api.get<User[]>('/users').subscribe({
        next: (response) => this.users.set(response),
        error: (err) => this.error.set(formatApiError(err))
      });
    }
    this.load();
  }

  ngOnDestroy(): void {
    this.clearImageUrls();
  }

  load(): void {
    const value = this.filterForm.getRawValue();
    this.api
      .get<Classification[]>('/classifications', {
        userId: this.auth.isAdmin() && value.userId ? Number(value.userId) : undefined,
        from: value.from || undefined,
        to: value.to || undefined
      })
      .subscribe({
        next: (response) => {
          this.history.set(response);
          this.loadImages(response);
        },
        error: (err) => this.error.set(formatApiError(err))
      });
  }

  imageUrl(imageId: number): string {
    return this.imageUrls()[imageId] || '';
  }

  private loadImages(items: Classification[]): void {
    this.clearImageUrls();

    if (items.length === 0) {
      return;
    }

    forkJoin(
      items.map((item) =>
        this.api.getBlob(`/files/images/${item.imageId}/content`).pipe(
          map((blob) => ({ imageId: item.imageId, url: URL.createObjectURL(blob) })),
          catchError(() => of({ imageId: item.imageId, url: '' }))
        )
      )
    ).subscribe((results) => {
      const nextUrls: Record<number, string> = {};
      for (const result of results) {
        if (result.url) {
          nextUrls[result.imageId] = result.url;
        }
      }
      this.imageUrls.set(nextUrls);
    });
  }

  private clearImageUrls(): void {
    Object.values(this.imageUrls()).forEach((url) => URL.revokeObjectURL(url));
    this.imageUrls.set({});
  }
}
