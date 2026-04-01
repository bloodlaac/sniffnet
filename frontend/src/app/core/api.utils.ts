import { ApiErrorResponse } from './api.models';

export function formatApiError(error: unknown): string {
  const response = (error as { error?: ApiErrorResponse })?.error;
  if (!response) {
    return 'Не удалось выполнить запрос. Попробуйте еще раз.';
  }

  if (response.validationErrors && Object.keys(response.validationErrors).length > 0) {
    return Object.entries(response.validationErrors)
      .map(([field, message]) => `${field}: ${message}`)
      .join('\n');
  }

  return response.message || 'Неизвестная ошибка сервера';
}
