import { CommonModule, DecimalPipe, KeyValuePipe } from '@angular/common';
import { Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { ApiService } from '../core/api.service';
import { Classification, Dataset, Model } from '../core/api.models';
import { formatApiError } from '../core/api.utils';

@Component({
  selector: 'app-classification-page',
  standalone: true,
  imports: [CommonModule, DecimalPipe, KeyValuePipe],
  template: `
    @if (error()) {
      <div class="error-banner">{{ error() }}</div>
    }

    <section class="classification-grid">
      <article class="card">
        <div class="section-head">
          <div>
            <p class="eyebrow">Inference</p>
            <h2>Проверка по фото</h2>
          </div>
          <label class="dataset-filter">
            <span>Датасет</span>
            <select [value]="datasetFilter()" (change)="changeDataset($any($event.target).value)">
              <option value="">Все</option>
              @for (dataset of datasets(); track dataset.id) {
                <option [value]="dataset.id">{{ dataset.name }}</option>
              }
            </select>
          </label>
        </div>

        <div class="model-list">
          @for (model of models(); track model.id) {
            <button
              type="button"
              class="model-card"
              [class.active]="selectedModelId() === model.id"
              (click)="pickModel(model.id)"
            >
              <div class="model-top">
                <strong>{{ model.name }}</strong>
                <span>{{ model.datasetName }}</span>
              </div>
              <div class="metric-line">
                <span>Val acc</span>
                <strong>
                  @if (model.metrics?.validationAccuracy !== null && model.metrics?.validationAccuracy !== undefined) {
                    {{ model.metrics?.validationAccuracy | number: '1.2-2' }}
                  } @else {
                    метрики отсутствуют
                  }
                </strong>
              </div>
            </button>
          }
        </div>
      </article>

      <article class="card">
        <p class="eyebrow">Upload</p>
        <h2>Отправка изображения</h2>

        @if (selectedModel(); as model) {
          <div class="selected-model card-shell">
            <div class="selected-model-head">
              <div>
                <span class="selected-label">Выбранная модель</span>
                <strong>{{ model.name }}</strong>
              </div>
              <span class="selected-dataset">{{ model.datasetName }}</span>
            </div>

            <div class="selected-metrics">
              <div>
                <span>Точность</span>
                <strong>
                  @if (model.metrics?.validationAccuracy !== null && model.metrics?.validationAccuracy !== undefined) {
                    {{ model.metrics?.validationAccuracy | number: '1.2-2' }}
                  } @else {
                    метрики отсутствуют
                  }
                </strong>
              </div>
              <div>
                <span>Потери</span>
                <strong>
                  @if (model.metrics?.validationLoss !== null && model.metrics?.validationLoss !== undefined) {
                    {{ model.metrics?.validationLoss | number: '1.2-2' }}
                  } @else {
                    метрики отсутствуют
                  }
                </strong>
              </div>
            </div>
          </div>
        } @else {
          <div class="selection-hint">
            Выберите модель слева.
          </div>
        }

        <form class="form-grid" (submit)="$event.preventDefault(); submit()">
          @if (!previewUrl()) {
            <label class="upload-box">
              <input type="file" accept=".jpg,.jpeg,.png,image/png,image/jpeg" (change)="handleFile($event)" />
              <span>Выбрать JPG или PNG</span>
              <small>Максимум 5 MB</small>
            </label>
          } @else {
            <div class="selected-file-bar">
              <div>
                <span class="selected-label">Выбранный файл</span>
                <strong>{{ selectedFileName() }}</strong>
              </div>

              <div class="file-actions">
                <label class="ghost-button inline-upload-button">
                  <input type="file" accept=".jpg,.jpeg,.png,image/png,image/jpeg" (change)="handleFile($event)" />
                  <span>Заменить</span>
                </label>
                <button type="button" class="ghost-button danger-button" (click)="clearFile()">
                  Убрать
                </button>
              </div>
            </div>
          }

          @if (previewUrl()) {
            <div class="preview-frame">
              <img class="preview-image" [src]="previewUrl()" alt="preview" />
            </div>
          }

          <button type="submit" class="primary-button" [disabled]="submitting()">
            {{ submitting() ? 'Отправляем...' : 'Запустить классификацию' }}
          </button>
        </form>

        @if (result(); as item) {
          <div class="result-box">
            <div class="result-head">
              <div>
                <p class="eyebrow">Result</p>
                <h3>{{ item.predictedClass || 'Нет класса' }}</h3>
              </div>
              <strong>
                @if (item.confidence !== null && item.confidence !== undefined) {
                  {{ item.confidence | number: '1.2-2' }}
                } @else {
                  значение отсутствует
                }
              </strong>
            </div>

            <div class="probability-list">
              @for (entry of item.probabilities | keyvalue; track entry.key) {
                <div class="probability-item">
                  <span>{{ entry.key }}</span>
                  <strong>{{ entry.value | number: '1.2-2' }}</strong>
                </div>
              }
            </div>

          </div>
        }
      </article>
    </section>
  `,
  styles: `
    .classification-grid {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 1rem;
    }

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

    .model-list {
      display: grid;
      gap: 0.8rem;
    }

    .model-card {
      text-align: left;
      width: 100%;
      padding: 1rem;
      border-radius: 0.8rem;
      border: 1px solid rgba(28, 71, 44, 0.12);
      background: var(--color-surface-tint);
      transition: border-color 160ms ease;
    }

    .model-card.active {
      border-color: var(--color-accent);
      background: #e8f3e5;
    }

    .model-top {
      display: grid;
      gap: 0.25rem;
      margin-bottom: 0.9rem;
    }

    .model-top span {
      color: var(--color-text-muted);
    }

    .card-shell,
    .selection-hint {
      margin-bottom: 1rem;
      padding: 1rem;
      border-radius: 0.8rem;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.12);
    }

    .selected-model {
      display: grid;
      gap: 1rem;
    }

    .selected-model-head,
    .selected-metrics,
    .metric-line,
    .result-head,
    .probability-item {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
    }

    .selected-label,
    .selected-metrics span,
    .selected-dataset {
      color: var(--color-text-muted);
    }

    .selected-label {
      display: block;
      margin-bottom: 0.35rem;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .selected-metrics > div {
      flex: 1;
      padding: 0.85rem 0.9rem;
      border-radius: 0.8rem;
      background: #ffffff;
      border: 1px solid var(--color-border);
    }

    .selected-metrics > div span {
      display: block;
      margin-bottom: 0.35rem;
      font-size: 0.85rem;
    }

    .selected-file-bar {
      display: flex;
      justify-content: space-between;
      gap: 1rem;
      align-items: center;
      padding: 1rem;
      border-radius: 0.8rem;
      background: var(--color-surface-tint);
      border: 1px solid rgba(28, 71, 44, 0.12);
    }

    .file-actions {
      display: flex;
      gap: 0.75rem;
      align-items: center;
      flex-wrap: wrap;
    }

    .inline-upload-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      text-decoration: none;
    }

    .inline-upload-button input {
      display: none;
    }

    .danger-button {
      color: var(--color-danger-text);
      border-color: rgba(165, 63, 31, 0.18);
      background: var(--color-danger-bg);
    }

    .upload-box {
      display: grid;
      place-items: center;
      gap: 0.3rem;
      min-height: 11rem;
      border: 1px dashed var(--color-accent);
      border-radius: 0.8rem;
      background: var(--color-surface-tint);
      cursor: pointer;
      text-align: center;
    }

    .upload-box input {
      display: none;
    }

    .upload-box small {
      color: var(--color-text-muted);
    }

    .preview-frame {
      display: grid;
      place-items: center;
      min-height: 18rem;
      padding: 1rem;
      border-radius: 0.8rem;
      background: #ffffff;
      border: 1px solid var(--color-border);
    }

    .preview-image,
    .result-image {
      width: 100%;
      border-radius: 0.8rem;
      object-fit: contain;
      max-height: 18rem;
      background: var(--color-surface-tint);
    }

    .result-box {
      display: grid;
      gap: 1rem;
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--color-border);
    }

    .result-head h3 {
      margin: 0.2rem 0 0;
    }

    .probability-list {
      display: grid;
      gap: 0.55rem;
    }

    .probability-item {
      padding: 0.8rem 0.9rem;
      border-radius: 0.8rem;
      background: var(--color-surface-tint);
    }

    @media (max-width: 1120px) {
      .classification-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .selected-model-head,
      .selected-metrics,
      .selected-file-bar {
        flex-direction: column;
        align-items: stretch;
      }

      .file-actions {
        width: 100%;
      }

      .file-actions > * {
        flex: 1;
      }
    }
  `
})
export class ClassificationPageComponent implements OnDestroy {
  readonly api = inject(ApiService);

  readonly datasets = signal<Dataset[]>([]);
  readonly models = signal<Model[]>([]);
  readonly selectedModelId = signal<number | null>(null);
  readonly datasetFilter = signal('');
  readonly previewUrl = signal('');
  readonly selectedFileName = signal('');
  readonly submitting = signal(false);
  readonly error = signal('');
  readonly result = signal<Classification | null>(null);
  private selectedFile: File | null = null;
  readonly selectedModel = computed(() => this.models().find((item) => item.id === this.selectedModelId()) ?? null);

  constructor() {
    this.loadDatasets();
    this.loadModels();
  }

  ngOnDestroy(): void {
    this.revokeUrl(this.previewUrl());
  }

  pickModel(modelId: number): void {
    this.selectedModelId.set(modelId);
  }

  changeDataset(value: string): void {
    this.datasetFilter.set(value);
    this.loadModels();
  }

  handleFile(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    this.selectedFile = file;
    this.selectedFileName.set(file?.name ?? '');
    this.setPreviewUrl(file ? URL.createObjectURL(file) : '');
  }

  clearFile(): void {
    this.selectedFile = null;
    this.selectedFileName.set('');
    this.setPreviewUrl('');
  }

  submit(): void {
    if (!this.selectedModelId() || !this.selectedFile) {
      this.error.set('Нужно выбрать модель и файл изображения.');
      return;
    }

    this.submitting.set(true);
    this.error.set('');
    this.result.set(null);

    const formData = new FormData();
    formData.append('modelId', String(this.selectedModelId()));
    formData.append('file', this.selectedFile);

    this.api.postFormData<Classification>('/classifications', formData).subscribe({
      next: (response) => {
        this.submitting.set(false);
        this.result.set(response);
      },
      error: (err) => {
        this.submitting.set(false);
        this.error.set(formatApiError(err));
      }
    });
  }

  private loadModels(): void {
    this.api.get<Model[]>('/models', {
      datasetId: this.datasetFilter() ? Number(this.datasetFilter()) : undefined
    }).subscribe({
      next: (response) => {
        const models = response.filter((item) => item.availableForInference);
        this.models.set(models);

        if (!models.some((item) => item.id === this.selectedModelId())) {
          this.selectedModelId.set(null);
        }
      },
      error: (err) => this.error.set(formatApiError(err))
    });
  }

  private loadDatasets(): void {
    this.api.get<Dataset[]>('/datasets').subscribe({
      next: (response) => this.datasets.set(response),
      error: (err) => this.error.set(formatApiError(err))
    });
  }

  private setPreviewUrl(nextUrl: string): void {
    const currentUrl = this.previewUrl();
    this.revokeUrl(currentUrl);
    this.previewUrl.set(nextUrl);
  }

  private revokeUrl(url: string): void {
    if (url) {
      URL.revokeObjectURL(url);
    }
  }
}
