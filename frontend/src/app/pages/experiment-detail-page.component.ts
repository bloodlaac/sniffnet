import { CommonModule, DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Experiment } from '../core/api.models';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-experiment-detail-page',
  standalone: true,
  imports: [CommonModule, RouterLink, DatePipe, DecimalPipe],
  template: `
    <a routerLink="/experiments" class="back-link">← Назад к списку</a>

    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    @if (experiment(); as item) {
      <section class="detail-grid">
        <article class="card">
          <p class="eyebrow">Experiment #{{ item.id }}</p>
          <h2>{{ item.datasetName }}</h2>
          <div class="info-grid">
            <div><span>Статус</span><strong>{{ item.status }}</strong></div>
            <div><span>Автор</span><strong>{{ item.username }}</strong></div>
            <div><span>Старт</span><strong>{{ item.startTime | date: 'dd.MM.yyyy HH:mm' }}</strong></div>
            <div><span>Завершение</span><strong>{{ item.endTime ? (item.endTime | date: 'dd.MM.yyyy HH:mm') : 'В процессе' }}</strong></div>
          </div>
        </article>

        <article class="card">
          <p class="eyebrow">Config</p>
          <h2>Параметры обучения</h2>
          <div class="info-grid">
            <div><span>Epochs</span><strong>{{ item.config.epochsNum }}</strong></div>
            <div><span>Batch size</span><strong>{{ item.config.batchSize }}</strong></div>
            <div><span>Learning rate</span><strong>{{ item.config.learningRate }}</strong></div>
            <div><span>Validation split</span><strong>{{ item.config.validationSplit }}</strong></div>
            <div><span>Optimizer</span><strong>{{ item.config.optimizer }}</strong></div>
            <div><span>Loss</span><strong>{{ item.config.lossFunction }}</strong></div>
          </div>
        </article>

        <article class="card">
          <p class="eyebrow">Model</p>
          <h2>{{ item.model?.name || 'Модель еще не создана' }}</h2>
          @if (item.model) {
            <div class="info-grid">
              <div><span>Params</span><strong>{{ item.model.paramsNum }}</strong></div>
              <div><span>Training time</span><strong>{{ item.model.trainingTimeSeconds }} sec</strong></div>
              <div><span>Inference</span><strong>{{ item.model.availableForInference ? 'Да' : 'Нет' }}</strong></div>
              <div><span>Experiment ID</span><strong>{{ item.model.experimentId }}</strong></div>
            </div>
          }
        </article>

        <article class="card">
          <p class="eyebrow">Metrics</p>
          <h2>Качество обучения</h2>
          @if (item.metrics) {
            <div class="info-grid">
              <div><span>Train accuracy</span><strong>{{ item.metrics.trainAccuracy | number: '1.2-2' }}</strong></div>
              <div><span>Train loss</span><strong>{{ item.metrics.trainLoss | number: '1.2-2' }}</strong></div>
              <div><span>Val accuracy</span><strong>{{ item.metrics.validationAccuracy | number: '1.2-2' }}</strong></div>
              <div><span>Val loss</span><strong>{{ item.metrics.validationLoss | number: '1.2-2' }}</strong></div>
            </div>
          } @else {
            <p class="muted">Метрики пока отсутствуют.</p>
          }
        </article>
      </section>
    }
  `,
  styles: `
    .back-link {
      display: inline-block;
      margin-bottom: 1rem;
      color: var(--color-accent-strong);
      text-decoration: none;
    }

    .detail-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
    }

    .card h2 {
      margin: 0.25rem 0 1rem;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.9rem;
    }

    .info-grid div {
      padding: 0.95rem;
      border-radius: 1rem;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.08);
    }

    .info-grid span {
      display: block;
      color: var(--color-text-muted);
      font-size: 0.85rem;
      margin-bottom: 0.3rem;
    }

    .muted {
      margin: 0;
      color: var(--color-text-muted);
    }

    @media (max-width: 1024px) {
      .detail-grid,
      .info-grid {
        grid-template-columns: 1fr;
      }
    }
  `
})
export class ExperimentDetailPageComponent {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);

  readonly experiment = signal<Experiment | null>(null);
  readonly error = signal('');

  constructor() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.get<Experiment>(`/experiments/${id}`).subscribe({
      next: (response) => this.experiment.set(response),
      error: (err) => this.error.set(formatApiError(err))
    });
  }
}
