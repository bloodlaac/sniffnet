import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../core/api.service';
import { Classification, Dataset, Experiment, Model } from '../core/api.models';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe, DecimalPipe],
  template: `
    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    <section class="stat-grid">
      <article class="card stat-card">
        <p>Датасеты</p>
        <strong>{{ datasets().length }}</strong>
        <span>Доступно для запуска обучения</span>
      </article>
      <article class="card stat-card">
        <p>Модели</p>
        <strong>{{ totalModels() }}</strong>
        <span>Готовы к инференсу</span>
      </article>
      <article class="card stat-card">
        <p>Эксперименты</p>
        <strong>{{ totalExperiments() }}</strong>
        <span>Последние запуски обучения</span>
      </article>
      <article class="card stat-card">
        <p>Классификации</p>
        <strong>{{ totalHistory() }}</strong>
        <span>Последние обращения к сервису</span>
      </article>
    </section>

    <section class="panel-grid">
      <article class="card panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Datasets</p>
            <h2>Доступные датасеты</h2>
          </div>
          <a routerLink="/experiments">Новый эксперимент</a>
        </div>

        <div class="list">
          @for (dataset of datasets(); track dataset.id) {
            <div class="list-item">
              <div>
                <strong>{{ dataset.name }}</strong>
                <p>{{ dataset.source }}</p>
              </div>
              <span>{{ dataset.classesNum }} classes</span>
            </div>
          }
        </div>
      </article>

      <article class="card panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Experiments</p>
            <h2>Последние запуски</h2>
          </div>
          <a routerLink="/experiments">Смотреть все</a>
        </div>

        <div class="list">
          @for (experiment of experiments(); track experiment.id) {
            <a class="list-item link-row" [routerLink]="['/experiments', experiment.id]">
              <div>
                <strong>#{{ experiment.id }} · {{ experiment.datasetName }}</strong>
                <p>{{ experiment.startTime | date: 'dd.MM.yyyy HH:mm' }}</p>
              </div>
              <span class="status-chip" [class.success]="experiment.status === 'COMPLETED'" [class.warn]="experiment.status === 'RUNNING'">
                {{ experiment.status }}
              </span>
            </a>
          }
        </div>
      </article>

      <article class="card panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Models</p>
            <h2>Готовые модели</h2>
          </div>
          <a routerLink="/classification">К проверке фото</a>
        </div>

        <div class="list">
          @for (model of models(); track model.id) {
            <div class="list-item">
              <div>
                <strong>{{ model.name }}</strong>
                <p>{{ model.datasetName }}</p>
              </div>
              <span>
                @if (model.metrics?.validationAccuracy !== null && model.metrics?.validationAccuracy !== undefined) {
                  {{ model.metrics?.validationAccuracy | number: '1.2-2' }}
                } @else {
                  метрики отсутствуют
                }
              </span>
            </div>
          }
        </div>
      </article>

      <article class="card panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">History</p>
            <h2>Недавние результаты</h2>
          </div>
          <a routerLink="/history">Полная история</a>
        </div>

        <div class="list">
          @for (item of history(); track item.id) {
            <div class="list-item">
              <div>
                <strong>{{ item.predictedClass || 'Ожидание ответа' }}</strong>
                <p>{{ item.modelName }}</p>
              </div>
              <span>
                @if (item.confidence !== null && item.confidence !== undefined) {
                  {{ item.confidence | number: '1.2-2' }}
                } @else {
                  значение отсутствует
                }
              </span>
            </div>
          }
        </div>
      </article>
    </section>
  `,
  styles: `
    .stat-grid,
    .panel-grid {
      display: grid;
      gap: 1rem;
    }

    .stat-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-bottom: 1rem;
    }

    .panel-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .stat-card strong {
      display: block;
      margin: 0.6rem 0 0.4rem;
      font-size: 2.6rem;
    }

    .stat-card p,
    .stat-card span,
    .panel-head p,
    .list-item p {
      margin: 0;
    }

    .stat-card span,
    .panel-head p,
    .list-item p {
      color: var(--color-text-muted);
    }

    .panel {
      padding: 1.3rem;
    }

    .panel-head {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
      margin-bottom: 1rem;
    }

    .panel-head h2 {
      margin: 0.25rem 0 0;
      font-size: 1.3rem;
    }

    .panel-head a {
      color: var(--color-accent-strong);
      text-decoration: none;
    }

    .list {
      display: grid;
      gap: 0.75rem;
    }

    .list-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 0.95rem 1rem;
      border-radius: 1rem;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.08);
    }

    .link-row {
      color: inherit;
      text-decoration: none;
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

    .status-chip.warn {
      background: var(--color-warning-bg);
      color: var(--color-warning-text);
    }

    @media (max-width: 1120px) {
      .stat-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .panel-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 640px) {
      .stat-grid {
        grid-template-columns: 1fr;
      }
    }
  `
})
export class DashboardPageComponent {
  private readonly api = inject(ApiService);

  readonly datasets = signal<Dataset[]>([]);
  readonly models = signal<Model[]>([]);
  readonly experiments = signal<Experiment[]>([]);
  readonly history = signal<Classification[]>([]);
  readonly totalModels = signal(0);
  readonly totalExperiments = signal(0);
  readonly totalHistory = signal(0);
  readonly error = signal('');

  constructor() {
    this.load();
  }

  private load(): void {
    forkJoin({
      datasets: this.api.get<Dataset[]>('/datasets'),
      models: this.api.get<Model[]>('/models'),
      experiments: this.api.get<Experiment[]>('/experiments'),
      history: this.api.get<Classification[]>('/classifications')
    }).subscribe({
      next: ({ datasets, models, experiments, history }) => {
        const readyModels = models.filter((model) => model.availableForInference);
        this.datasets.set(datasets);
        this.models.set(readyModels);
        this.experiments.set(experiments);
        this.history.set(history);
        this.totalModels.set(readyModels.length);
        this.totalExperiments.set(experiments.length);
        this.totalHistory.set(history.length);
      },
      error: (err) => this.error.set(formatApiError(err))
    });
  }
}
