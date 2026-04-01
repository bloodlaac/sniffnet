export interface ApiErrorResponse {
  timestamp: string;
  status: number;
  error: string;
  message: string;
  path: string;
  validationErrors?: Record<string, string> | null;
}

export interface AuthResponse {
  token: string;
  userId: number;
  username: string;
  email: string;
  role: UserRole;
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  createdAt?: string;
}

export interface Dataset {
  id: number;
  name: string;
  classesNum: number;
  source: string;
}

export interface TrainingConfig {
  id?: number;
  epochsNum: number;
  batchSize: number;
  learningRate: number;
  optimizer: string;
  lossFunction: string;
  validationSplit: number;
  layersNum?: number | null;
  neuronsNum?: number | null;
}

export interface Metric {
  id: number;
  trainAccuracy: number;
  trainLoss: number;
  validationAccuracy: number;
  validationLoss: number;
  detailsJson?: string | null;
}

export interface Model {
  id: number;
  name: string;
  datasetId: number;
  datasetName: string;
  configId: number;
  experimentId: number;
  paramsNum: number;
  trainingTimeSeconds: number;
  availableForInference: boolean;
  weightsPath?: string | null;
  createdAt?: string;
  metrics?: Metric | null;
}

export interface Experiment {
  id: number;
  status: ExperimentStatus;
  startTime: string;
  endTime?: string | null;
  reportPath?: string | null;
  errorMessage?: string | null;
  datasetId: number;
  datasetName: string;
  userId: number;
  username: string;
  config: TrainingConfig;
  model?: Model | null;
  metrics?: Metric | null;
}

export interface UploadedImage {
  id: number;
  userId: number;
  originalFilename: string;
  storedFilename: string;
  contentType: string;
  sizeBytes: number;
  storagePath: string;
  uploadedAt: string;
}

export interface Classification {
  id: number;
  status: ClassificationStatus;
  createdAt: string;
  completedAt?: string | null;
  predictedClass?: string | null;
  confidence?: number | null;
  modelId: number;
  modelName: string;
  imageId: number;
  imagePath: string;
  probabilities: Record<string, number>;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  createdAt: string;
}

export type UserRole = 'ROLE_USER' | 'ROLE_ADMIN';
export type ExperimentStatus = 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CREATED';
export type ClassificationStatus = 'CREATED' | 'COMPLETED' | 'FAILED';
