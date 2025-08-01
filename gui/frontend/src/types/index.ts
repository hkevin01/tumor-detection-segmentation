// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

// Patient Types
export interface Patient {
  id: string;
  name: string;
  date_of_birth?: string;
  gender?: string;
  medical_record_number?: string;
  created_at: string;
  updated_at?: string;
  study_count?: number;
}

export interface PatientCreate {
  name: string;
  date_of_birth?: string;
  gender?: string;
  medical_record_number?: string;
}

// Study Types
export type StudyStatus = 'uploaded' | 'processing' | 'completed' | 'failed';

export interface Study {
  id: string;
  patient_id: string;
  study_date: string;
  modality: string;
  description?: string;
  status: StudyStatus;
  file_path?: string;
  created_at: string;
  updated_at?: string;
  has_ai_results: boolean;
  latest_prediction?: PredictionResult;
}

export interface StudyCreate {
  patient_id: string;
  study_date: string;
  modality: string;
  description?: string;
  file_path?: string;
}

// AI Prediction Types
export interface PredictionResult {
  id: number;
  study_id: string;
  model_id: string;
  prediction: string;
  confidence: number;
  tumor_volume?: number;
  coordinates?: number[][];
  processing_time: number;
  created_at: string;
}

export interface PredictionRequest {
  study_id: string;
  model_id?: string;
}

// AI Model Types
export interface AIModel {
  id: string;
  name: string;
  description?: string;
  version?: string;
  accuracy: number;
  file_path: string;
  is_active: boolean;
  created_at: string;
}

// Report Types
export interface Report {
  id: string;
  study_id: string;
  template: string;
  findings: {
    tumor_detected: boolean;
    confidence?: number;
    tumor_volume?: number;
    coordinates?: number[][];
    model_used?: string;
  };
  recommendations: string;
  report_path?: string;
  generated_by: string;
  created_at: string;
}

export interface ReportRequest {
  study_id: string;
  template?: string;
}

// Upload Types
export interface UploadResponse {
  message: string;
  study_id: string;
  patient_id: string;
  filename: string;
  file_path: string;
  size: number;
  upload_time: string;
  status: string;
}

// Health Check Types
export interface HealthStatus {
  status: string;
  device?: string;
  timestamp: string;
  service?: string;
}

// Dashboard Types
export interface DashboardStats {
  total_patients: number;
  total_studies: number;
  studies_today: number;
  ai_analyses_completed: number;
  success_rate: number;
  average_processing_time: number;
}

// File Upload Types
export interface FileUploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

// Error Types
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Navigation Types
export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon: any; // React component type
}

// Theme Types
export interface CustomTheme {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  border: string;
}
