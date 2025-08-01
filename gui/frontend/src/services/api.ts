import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  Patient, PatientCreate,
  Study, StudyCreate,
  PredictionResult, PredictionRequest,
  Report, ReportRequest,
  AIModel,
  UploadResponse,
  HealthStatus,
  ApiError
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth tokens
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async getHealth(): Promise<HealthStatus> {
    const response = await this.api.get<HealthStatus>('/api/health');
    return response.data;
  }

  // Patient Management
  async getPatients(): Promise<Patient[]> {
    const response = await this.api.get<{ patients: Patient[]; count: number }>('/api/patients');
    return response.data.patients;
  }

  async createPatient(patient: PatientCreate): Promise<Patient> {
    const response = await this.api.post<Patient>('/api/patients', patient);
    return response.data;
  }

  async getPatient(patientId: string): Promise<Patient> {
    const response = await this.api.get<Patient>(`/api/patients/${patientId}`);
    return response.data;
  }

  // Study Management
  async getStudies(patientId?: string): Promise<Study[]> {
    const params = patientId ? { patient_id: patientId } : {};
    const response = await this.api.get<{ studies: Study[]; count: number }>('/api/studies', { params });
    return response.data.studies;
  }

  async getStudy(studyId: string): Promise<{
    study: Study;
    predictions: PredictionResult[];
    reports: Report[];
  }> {
    const response = await this.api.get(`/api/studies/${studyId}`);
    return response.data;
  }

  async createStudy(study: StudyCreate): Promise<Study> {
    const response = await this.api.post<Study>('/api/studies', study);
    return response.data;
  }

  // File Upload
  async uploadFile(
    file: File,
    patientId?: string,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (patientId) {
      formData.append('patient_id', patientId);
    }

    const response = await this.api.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentage);
        }
      },
    });

    return response.data;
  }

  // AI Predictions
  async runPrediction(request: PredictionRequest): Promise<{
    message: string;
    result: PredictionResult;
  }> {
    const response = await this.api.post('/api/predict', null, {
      params: request,
    });
    return response.data;
  }

  async getPredictions(studyId: string): Promise<PredictionResult[]> {
    const response = await this.api.get<PredictionResult[]>(`/api/predictions/${studyId}`);
    return response.data;
  }

  // AI Models
  async getModels(): Promise<AIModel[]> {
    const response = await this.api.get<{ models: AIModel[]; count: number }>('/api/models');
    return response.data.models;
  }

  // Reports
  async generateReport(request: ReportRequest): Promise<{
    message: string;
    report_id: string;
    report: Report;
  }> {
    const response = await this.api.post('/api/reports', null, {
      params: request,
    });
    return response.data;
  }

  async getReports(studyId?: string): Promise<Report[]> {
    const params = studyId ? { study_id: studyId } : {};
    const response = await this.api.get<{ reports: Report[]; count: number }>('/api/reports', { params });
    return response.data.reports;
  }

  async downloadReport(reportId: string): Promise<Blob> {
    const response = await this.api.get(`/api/reports/${reportId}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Dashboard Statistics
  async getDashboardStats(): Promise<any> {
    const response = await this.api.get('/api/dashboard/stats');
    return response.data;
  }

  // Utility method for handling API errors
  handleApiError(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
