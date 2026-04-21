import { formatApiError } from './api.utils';

describe('formatApiError', () => {
  it('formats validation errors and falls back for generic failures', () => {
    expect(
      formatApiError({
        error: {
          message: 'Validation failed',
          validationErrors: {
            username: 'already exists',
            email: 'invalid format'
          }
        }
      })
    ).toBe('username: already exists\nemail: invalid format');
    expect(formatApiError({ error: { message: 'Boom' } })).toBe('Boom');
    expect(formatApiError(null)).toBe('Не удалось выполнить запрос. Попробуйте еще раз.');
  });
});
