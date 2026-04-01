import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Dataset, Experiment, ExperimentStatus, User } from '../core/api.models';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-experiments-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, DatePipe, DecimalPipe],
  template: `
    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    <section class="page-grid">
      <article class="card">
        <div class="section-head">
          <div>
            <p class="eyebrow">Training</p>
            <h2>Новый эксперимент</h2>
          </div>
        </div>

        @if (!auth.isAdmin()) {
          <form class="form-grid" [formGroup]="form" (ngSubmit)="submit()">
            <label>
              Датасет
              <select formControlName="datasetId">
                <option value="">Выберите датасет</option>
                @for (dataset of datasets(); track dataset.id) {
                  <option [value]="dataset.id">{{ dataset.name }}</option>
                }
              </select>
            </label>

            <label>
              Эпохи
              <input type="number" formControlName="epochsNum" min="1" />
            </label>

            <label>
              Batch size
              <input type="number" formControlName="batchSize" min="1" />
            </label>

            <label>
              Learning rate
              <input type="number" formControlName="learningRate" min="0.000001" step="0.0001" />
            </label>

            <label>
              Optimizer
              <input type="text" formControlName="optimizer" />
            </label>

            <label>
              Loss function
              <input type="text" formControlName="lossFunction" />
            </label>

            <label>
              Validation split
              <input type="number" formControlName="validationSplit" min="0.01" max="0.99" step="0.01" />
            </label>

            <label>
              Layers
              <input type="number" formControlName="layersNum" min="1" />
            </label>

            <label>
              Neurons
              <input type="number" formControlName="neuronsNum" min="1" />
            </label>

            <button type="submit" class="primary-button" [disabled]="submitting()">
              {{ submitting() ? 'Создаем...' : 'Запустить эксперимент' }}
            </button>
          </form>
        } @else {
          <p class="muted">Администратор не может запускать обучение.</p>
        }
      </article>

      <article class="card">
        <div class="section-head filters">
          <div>
            <p class="eyebrow">History</p>
            <h2>Список экспериментов</h2>
          </div>

          <label class="filter-select">
            <span>Статус</span>
            <select [value]="statusFilter()" (change)="changeStatus($any($event.target).value)">
              <option value="">Все</option>
              @for (status of statuses; track status) {
                <option [value]="status">{{ status }}</option>
              }
            </select>
          </label>

          @if (auth.isAdmin()) {
            <label class="filter-select">
              <span>Пользователь</span>
              <select [value]="userFilter()" (change)="changeUser($any($event.target).value)">
                <option value="">Все</option>
                @for (user of users(); track user.id) {
                  <option [value]="user.id">{{ user.username }}</option>
                }
              </select>
            </label>
          }
        </div>

        <div class="experiment-list">
          @for (experiment of experiments(); track experiment.id) {
            <a class="experiment-card" [routerLink]="['/experiments', experiment.id]">
              <div class="experiment-head">
                <strong>#{{ experiment.id }} · {{ experiment.datasetName }}</strong>
                <div class="experiment-actions">
                  <span class="status-chip" [class.success]="experiment.status === 'COMPLETED'" [class.failed]="experiment.status === 'FAILED'">
                    {{ experiment.status }}
                  </span>
                  @if (auth.isAdmin()) {
                    <button
                      type="button"
                      class="ghost-button danger-button"
                      (click)="removeExperiment($event, experiment.id)"
                    >
                      Удалить
                    </button>
                  }
                </div>
              </div>

              <p>Старт: {{ experiment.startTime | date: 'dd.MM.yyyy HH:mm' }}</p>
              <p>Автор: {{ experiment.username }}</p>

              @if (experiment.metrics) {
                <div class="metric-row">
                  <span>Val acc</span>
                  <strong>{{ experiment.metrics.validationAccuracy | number: '1.2-2' }}</strong>
                </div>
              }
            </a>
          }
        </div>
      </article>
    </section>
  `,
  styles: `
    .page-grid {
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      gap: 1rem;
    }

    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .section-head h2 {
      margin: 0.25rem 0 0;
    }

    .muted {
      color: var(--color-text-muted);
      font-size: 0.92rem;
    }

    .filters {
      align-items: end;
    }

    .filter-select {
      min-width: 10rem;
    }

    .experiment-list {
      display: grid;
      gap: 0.85rem;
    }

    .experiment-card {
      display: grid;
      gap: 0.55rem;
      padding: 1rem;
      border-radius: 1.1rem;
      color: inherit;
      text-decoration: none;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.1);
    }

    .experiment-card p {
      margin: 0;
      color: var(--color-text-muted);
    }

    .experiment-head,
    .metric-row {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
    }

    .experiment-actions {
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }

    .status-chip {
      padding: 0.3rem 0.7rem;
      border-radius: 999px;
      background: var(--color-warning-bg);
      color: var(--color-warning-text);
      font-size: 0.82rem;
    }

    .status-chip.success {
      background: var(--color-success-bg);
      color: var(--color-success-text);
    }

    .status-chip.failed {
      background: var(--color-danger-bg);
      color: var(--color-danger-text);
    }

    .danger-button {
      color: var(--color-danger-text);
      border-color: rgba(165, 63, 31, 0.18);
      background: var(--color-danger-bg);
    }

    @media (max-width: 1120px) {
      .page-grid {
        grid-template-columns: 1fr;
      }
    }
  `
})
export class ExperimentsPageComponent {
  private readonly api = inject(ApiService);
  private readonly fb = inject(FormBuilder);
  readonly auth = inject(AuthService);

  readonly statuses: ExperimentStatus[] = ['CREATED', 'RUNNING', 'COMPLETED', 'FAILED'];
  readonly datasets = signal<Dataset[]>([]);
  readonly users = signal<User[]>([]);
  readonly experiments = signal<Experiment[]>([]);
  readonly statusFilter = signal('');
  readonly userFilter = signal('');
  readonly error = signal('');
  readonly submitting = signal(false);

  readonly form = this.fb.nonNullable.group({
    datasetId: [0, [Validators.min(1)]],
    epochsNum: [12, [Validators.required, Validators.min(1)]],
    batchSize: [16, [Validators.required, Validators.min(1)]],
    learningRate: [0.001, [Validators.required, Validators.min(0.000001)]],
    optimizer: ['Adam', [Validators.required]],
    lossFunction: ['CrossEntropyLoss', [Validators.required]],
    validationSplit: [0.2, [Validators.required, Validators.min(0.01), Validators.max(0.99)]],
    layersNum: [4],
    neuronsNum: [128]
  });

  constructor() {
    this.loadInitial();
  }

  changeStatus(value: string): void {
    this.statusFilter.set(value);
    this.loadExperiments();
  }

  changeUser(value: string): void {
    this.userFilter.set(value);
    this.loadExperiments();
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.error.set('');

    const raw = this.form.getRawValue();
    this.api.post<Experiment>('/experiments', {
      datasetId: Number(raw.datasetId),
      config: {
        epochsNum: Number(raw.epochsNum),
        batchSize: Number(raw.batchSize),
        learningRate: Number(raw.learningRate),
        optimizer: raw.optimizer,
        lossFunction: raw.lossFunction,
        validationSplit: Number(raw.validationSplit),
        layersNum: Number(raw.layersNum),
        neuronsNum: Number(raw.neuronsNum)
      }
    }).subscribe({
      next: () => {
        this.submitting.set(false);
        this.loadExperiments();
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(formatApiError(err));
      }
    });
  }

  removeExperiment(event: Event, experimentId: number): void {
    event.preventDefault();
    event.stopPropagation();

    if (!confirm(`Удалить эксперимент #${experimentId}?`)) {
      return;
    }

    this.api.delete(`/experiments/${experimentId}`).subscribe({
      next: () => this.loadExperiments(),
      error: (err) => this.error.set(formatApiError(err))
    });
  }

  private loadInitial(): void {
    forkJoin({
      datasets: this.api.get<Dataset[]>('/datasets'),
      experiments: this.api.get<Experiment[]>('/experiments'),
      users: this.auth.isAdmin() ? this.api.get<User[]>('/users') : of<User[]>([])
    }).subscribe({
      next: ({ datasets, experiments, users }) => {
        this.datasets.set(datasets);
        this.experiments.set(experiments);
        this.users.set(users);
      },
      error: (err) => this.error.set(formatApiError(err))
    });
  }

  private loadExperiments(): void {
    this.api
      .get<Experiment[]>('/experiments', {
        status: this.statusFilter() || undefined,
        userId: this.auth.isAdmin() && this.userFilter() ? Number(this.userFilter()) : undefined
      })
      .subscribe({
        next: (response) => this.experiments.set(response),
        error: (err) => this.error.set(formatApiError(err))
      });
  }
}
