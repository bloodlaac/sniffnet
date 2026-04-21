import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ApiService, provideHttpClient(), provideHttpClientTesting()]
    });

    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('builds urls, filters empty params and supports blob requests', () => {
    service.get('/models', { page: 2, search: '', mine: true, unused: null }).subscribe();

    const listRequest = httpMock.expectOne((request) => request.url === '/api/models');
    expect(listRequest.request.params.get('page')).toBe('2');
    expect(listRequest.request.params.get('mine')).toBe('true');
    expect(listRequest.request.params.has('search')).toBe(false);
    expect(listRequest.request.params.has('unused')).toBe(false);
    listRequest.flush([]);

    service.getBlob('/api/files/images/1/content').subscribe();

    const blobRequest = httpMock.expectOne('/api/files/images/1/content');
    expect(blobRequest.request.responseType).toBe('blob');
    expect(service.assetUrl('/api/files/images/1/content')).toBe('/api/files/images/1/content');
    blobRequest.flush(new Blob(['image']));
  });
});
