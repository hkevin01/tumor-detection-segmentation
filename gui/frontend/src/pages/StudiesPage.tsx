import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Upload as UploadIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { apiService } from '../services/api';
import { Study, Patient } from '../types';
import StudyViewer from '../components/StudyViewer';

const StudiesPage: React.FC = () => {
  const [studies, setStudies] = useState<Study[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedPatient, setSelectedPatient] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [selectedStudyUID, setSelectedStudyUID] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [studiesData, patientsData] = await Promise.all([
        apiService.getStudies(),
        apiService.getPatients(),
      ]);
      setStudies(studiesData);
      setPatients(patientsData);
    } catch (err) {
      setError(apiService.handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setUploadProgress(0);

      const result = await apiService.uploadFile(
        selectedFile,
        selectedPatient || undefined,
        (progress) => setUploadProgress(progress)
      );

      // Refresh studies list
      await fetchData();
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setSelectedPatient('');
      setUploadProgress(0);
    } catch (err) {
      setError(apiService.handleApiError(err));
    } finally {
      setUploading(false);
    }
  };

  const handleRunPrediction = async (studyId: string) => {
    try {
      await apiService.runPrediction({ study_id: studyId });
      await fetchData(); // Refresh to show updated status
    } catch (err) {
      setError(apiService.handleApiError(err));
    }
  };

  const handleViewStudy = (studyId: string) => {
    setSelectedStudyUID(studyId);
    setViewerOpen(true);
  };

  const handleCloseViewer = () => {
    setViewerOpen(false);
    setSelectedStudyUID(null);
  };

  const columns: GridColDef[] = [
    {
      field: 'id',
      headerName: 'Study ID',
      width: 120,
    },
    {
      field: 'patient_id',
      headerName: 'Patient',
      width: 120,
    },
    {
      field: 'modality',
      headerName: 'Modality',
      width: 100,
    },
    {
      field: 'description',
      headerName: 'Description',
      width: 200,
      flex: 1,
    },
    {
      field: 'study_date',
      headerName: 'Study Date',
      width: 120,
      valueFormatter: (params) => new Date(params.value).toLocaleDateString(),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={
            params.value === 'completed' ? 'success' :
            params.value === 'processing' ? 'warning' :
            params.value === 'failed' ? 'error' : 'default'
          }
          size="small"
        />
      ),
    },
    {
      field: 'has_ai_results',
      headerName: 'AI Results',
      width: 100,
      renderCell: (params) =>
        params.value ? <Chip label="Yes" color="primary" size="small" /> : 'No',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <IconButton size="small" onClick={() => handleViewStudy(params.row.id)}>
            <ViewIcon />
          </IconButton>
          {!params.row.has_ai_results && params.row.status === 'uploaded' && (
            <Button
              size="small"
              variant="outlined"
              onClick={() => handleRunPrediction(params.row.id)}
              sx={{ ml: 1 }}
            >
              Run AI
            </Button>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Medical Studies
        </Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialogOpen(true)}
        >
          Upload DICOM
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <DataGrid
            rows={studies}
            columns={columns}
            autoHeight
            loading={loading}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: { paginationModel: { pageSize: 10 } },
            }}
            disableRowSelectionOnClick
          />
        </CardContent>
      </Card>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => !uploading && setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload DICOM Study</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              select
              fullWidth
              label="Patient (Optional)"
              value={selectedPatient}
              onChange={(e) => setSelectedPatient(e.target.value)}
              SelectProps={{ native: true }}
              sx={{ mb: 2 }}
            >
              <option value="">Create new patient</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.name} ({patient.medical_record_number})
                </option>
              ))}
            </TextField>

            <input
              accept=".dcm,.dicom"
              style={{ display: 'none' }}
              id="file-upload"
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
            />
            <label htmlFor="file-upload">
              <Button
                variant="outlined"
                component="span"
                fullWidth
                sx={{ mb: 2 }}
              >
                {selectedFile ? selectedFile.name : 'Select DICOM File'}
              </Button>
            </label>

            {uploading && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Uploading: {uploadProgress}%
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)} disabled={uploading}>
            Cancel
          </Button>
          <Button
            onClick={handleFileUpload}
            variant="contained"
            disabled={!selectedFile || uploading}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>

      {/* Study Viewer */}
      {viewerOpen && selectedStudyUID && (
        <StudyViewer
          studyInstanceUID={selectedStudyUID}
          onClose={handleCloseViewer}
        />
      )}
    </Box>
  );
};

export default StudiesPage;
