import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Avatar,
  Divider,
  Switch,
  FormControlLabel,
  Slider,
  Badge,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Settings,
  CloudUpload,
  Visibility,
  Download,
  Share,
  Assessment,
  Timeline,
  TrendingUp,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Info,
  Psychology,
  Memory,
  Speed,
  Tune,
  ExpandMore,
  Close,
  FileUpload,
  Analysis,
  ModelTraining,
  DataUsage,
  BugReport,
  Security,
} from '@mui/icons-material';
import StudyViewer from '../components/StudyViewer';

interface AnalysisJob {
  id: string;
  name: string;
  studyId: string;
  modelId: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
  startTime: Date;
  endTime?: Date;
  confidence?: number;
  findings: string[];
  parameters: Record<string, any>;
}

interface AIModel {
  id: string;
  name: string;
  version: string;
  type: string;
  accuracy: number;
  speed: number;
  description: string;
  parameters: Record<string, any>;
  isActive: boolean;
}

const AIAnalysisPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedStudy, setSelectedStudy] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [analysisJobs, setAnalysisJobs] = useState<AnalysisJob[]>([]);
  const [models, setModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [configDialog, setConfigDialog] = useState(false);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [viewerDialog, setViewerDialog] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  
  // Analysis parameters
  const [batchSize, setBatchSize] = useState(1);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.85);
  const [enablePreprocessing, setEnablePreprocessing] = useState(true);
  const [enablePostprocessing, setEnablePostprocessing] = useState(true);

  // Demo data
  const demoModels: AIModel[] = [
    {
      id: 'unet-v2.1',
      name: 'U-Net Tumor Segmentation',
      version: '2.1',
      type: 'Segmentation',
      accuracy: 94.2,
      speed: 85,
      description: 'Advanced U-Net model for precise tumor boundary detection',
      parameters: { threshold: 0.5, nms: 0.4 },
      isActive: true,
    },
    {
      id: 'resnet-classifier',
      name: 'ResNet Tumor Classifier',
      version: '1.8',
      type: 'Classification',
      accuracy: 92.8,
      speed: 95,
      description: 'High-speed tumor detection and classification model',
      parameters: { confidence: 0.8, overlap: 0.3 },
      isActive: true,
    },
    {
      id: 'ensemble-v3',
      name: 'Ensemble Multi-Modal',
      version: '3.0',
      type: 'Ensemble',
      accuracy: 96.1,
      speed: 70,
      description: 'Combined model using multiple AI techniques for maximum accuracy',
      parameters: { voting: 'soft', weights: [0.4, 0.3, 0.3] },
      isActive: false,
    },
  ];

  const demoJobs: AnalysisJob[] = [
    {
      id: 'job-001',
      name: 'CT Chest Analysis',
      studyId: 'study-001',
      modelId: 'unet-v2.1',
      status: 'completed',
      progress: 100,
      startTime: new Date(Date.now() - 300000),
      endTime: new Date(Date.now() - 60000),
      confidence: 94.2,
      findings: ['No significant abnormalities detected', 'Image quality: Excellent'],
      parameters: { threshold: 0.85, preprocessing: true },
    },
    {
      id: 'job-002',
      name: 'MRI Brain Scan',
      studyId: 'study-002',
      modelId: 'resnet-classifier',
      status: 'running',
      progress: 67,
      startTime: new Date(Date.now() - 120000),
      findings: [],
      parameters: { confidence: 0.9, batch_size: 1 },
    },
    {
      id: 'job-003',
      name: 'CT Abdomen Analysis',
      studyId: 'study-003',
      modelId: 'ensemble-v3',
      status: 'queued',
      progress: 0,
      startTime: new Date(),
      findings: [],
      parameters: { ensemble_mode: 'voting', threshold: 0.8 },
    },
  ];

  useEffect(() => {
    setModels(demoModels);
    setAnalysisJobs(demoJobs);
  }, []);

  const steps = [
    {
      label: 'Select Study',
      description: 'Choose the medical study to analyze',
    },
    {
      label: 'Configure AI Model',
      description: 'Select and configure the AI analysis model',
    },
    {
      label: 'Set Parameters',
      description: 'Adjust analysis parameters and settings',
    },
    {
      label: 'Run Analysis',
      description: 'Execute the AI analysis and monitor progress',
    },
  ];

  const handleNext = () => {
    setCurrentStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setCurrentStep((prevStep) => prevStep - 1);
  };

  const handleReset = () => {
    setCurrentStep(0);
    setSelectedStudy('');
    setSelectedModel('');
  };

  const startAnalysis = async () => {
    if (!selectedStudy || !selectedModel) return;
    
    setLoading(true);
    
    // Simulate analysis start
    const newJob: AnalysisJob = {
      id: `job-${Date.now()}`,
      name: `Analysis ${Date.now()}`,
      studyId: selectedStudy,
      modelId: selectedModel,
      status: 'running',
      progress: 0,
      startTime: new Date(),
      findings: [],
      parameters: {
        batch_size: batchSize,
        confidence_threshold: confidenceThreshold,
        preprocessing: enablePreprocessing,
        postprocessing: enablePostprocessing,
      },
    };
    
    setAnalysisJobs(prev => [newJob, ...prev]);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setAnalysisJobs(prev => 
        prev.map(job => 
          job.id === newJob.id && job.progress < 100
            ? { ...job, progress: Math.min(job.progress + 10, 100) }
            : job
        )
      );
    }, 1000);
    
    // Complete after 10 seconds
    setTimeout(() => {
      clearInterval(progressInterval);
      setAnalysisJobs(prev => 
        prev.map(job => 
          job.id === newJob.id
            ? { 
                ...job, 
                status: 'completed', 
                progress: 100,
                endTime: new Date(),
                confidence: Math.random() * 20 + 80,
                findings: ['Analysis completed successfully', 'Suspicious region detected in sector 3']
              }
            : job
        )
      );
      setLoading(false);
    }, 10000);
  };

  const pauseJob = (jobId: string) => {
    setAnalysisJobs(prev => 
      prev.map(job => 
        job.id === jobId ? { ...job, status: 'paused' as const } : job
      )
    );
  };

  const resumeJob = (jobId: string) => {
    setAnalysisJobs(prev => 
      prev.map(job => 
        job.id === jobId ? { ...job, status: 'running' as const } : job
      )
    );
  };

  const stopJob = (jobId: string) => {
    setAnalysisJobs(prev => 
      prev.map(job => 
        job.id === jobId ? { ...job, status: 'failed' as const } : job
      )
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'error';
      case 'paused': return 'warning';
      case 'queued': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'running': return <Timeline color="primary" />;
      case 'failed': return <ErrorIcon color="error" />;
      case 'paused': return <Pause color="warning" />;
      case 'queued': return <Schedule color="action" />;
      default: return <Info />;
    }
  };

  const formatDuration = (start: Date, end?: Date) => {
    const endTime = end || new Date();
    const duration = endTime.getTime() - start.getTime();
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          AI Analysis Workflow
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Upload New Study">
            <Fab size="small" color="secondary" onClick={() => setUploadDialog(true)}>
              <CloudUpload />
            </Fab>
          </Tooltip>
          <Tooltip title="Model Configuration">
            <Fab size="small" color="primary" onClick={() => setConfigDialog(true)}>
              <Settings />
            </Fab>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Workflow Stepper */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Workflow
              </Typography>
              <Stepper activeStep={currentStep} orientation="vertical">
                {steps.map((step, index) => (
                  <Step key={step.label}>
                    <StepLabel>{step.label}</StepLabel>
                    <StepContent>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        {step.description}
                      </Typography>
                      
                      {index === 0 && (
                        <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                          <InputLabel>Select Study</InputLabel>
                          <Select
                            value={selectedStudy}
                            label="Select Study"
                            onChange={(e) => setSelectedStudy(e.target.value)}
                          >
                            <MenuItem value="study-001">CT Chest - Patient A</MenuItem>
                            <MenuItem value="study-002">MRI Brain - Patient B</MenuItem>
                            <MenuItem value="study-003">CT Abdomen - Patient C</MenuItem>
                            <MenuItem value="study-004">MRI Spine - Patient D</MenuItem>
                          </Select>
                        </FormControl>
                      )}
                      
                      {index === 1 && (
                        <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                          <InputLabel>Select AI Model</InputLabel>
                          <Select
                            value={selectedModel}
                            label="Select AI Model"
                            onChange={(e) => setSelectedModel(e.target.value)}
                          >
                            {models.map((model) => (
                              <MenuItem key={model.id} value={model.id}>
                                {model.name} v{model.version}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      )}
                      
                      {index === 2 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Confidence Threshold
                          </Typography>
                          <Slider
                            value={confidenceThreshold}
                            onChange={(e, v) => setConfidenceThreshold(v as number)}
                            step={0.05}
                            min={0.5}
                            max={1.0}
                            valueLabelDisplay="auto"
                            valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                          />
                          
                          <FormControlLabel
                            control={
                              <Switch
                                checked={enablePreprocessing}
                                onChange={(e) => setEnablePreprocessing(e.target.checked)}
                              />
                            }
                            label="Enable Preprocessing"
                            sx={{ display: 'block', mt: 1 }}
                          />
                          
                          <FormControlLabel
                            control={
                              <Switch
                                checked={enablePostprocessing}
                                onChange={(e) => setEnablePostprocessing(e.target.checked)}
                              />
                            }
                            label="Enable Postprocessing"
                            sx={{ display: 'block' }}
                          />
                        </Box>
                      )}
                      
                      {index === 3 && (
                        <Box sx={{ mb: 2 }}>
                          <Button
                            variant="contained"
                            onClick={startAnalysis}
                            disabled={!selectedStudy || !selectedModel || loading}
                            startIcon={<PlayArrow />}
                            fullWidth
                          >
                            Start Analysis
                          </Button>
                        </Box>
                      )}
                      
                      <Box>
                        <Button
                          disabled={index === 0}
                          onClick={handleBack}
                          sx={{ mr: 1 }}
                        >
                          Back
                        </Button>
                        <Button
                          variant="contained"
                          onClick={handleNext}
                          disabled={
                            (index === 0 && !selectedStudy) ||
                            (index === 1 && !selectedModel) ||
                            index === steps.length - 1
                          }
                        >
                          {index === steps.length - 1 ? 'Finish' : 'Next'}
                        </Button>
                      </Box>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
              
              {currentStep === steps.length && (
                <Paper square elevation={0} sx={{ p: 3 }}>
                  <Typography>All steps completed - Analysis ready to run!</Typography>
                  <Button onClick={handleReset} sx={{ mt: 1, mr: 1 }}>
                    Reset Workflow
                  </Button>
                </Paper>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Jobs and Models */}
        <Grid item xs={12} lg={8}>
          <Grid container spacing={2}>
            {/* Active Jobs */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                    <Typography variant="h6">
                      Analysis Jobs
                    </Typography>
                    <Button startIcon={<Refresh />} size="small">
                      Refresh
                    </Button>
                  </Box>
                  
                  {analysisJobs.map((job) => (
                    <Paper key={job.id} sx={{ p: 2, mb: 2 }} variant="outlined">
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                        <Box flex={1}>
                          <Box display="flex" alignItems="center" gap={1} sx={{ mb: 1 }}>
                            {getStatusIcon(job.status)}
                            <Typography variant="subtitle1">{job.name}</Typography>
                            <Chip 
                              label={job.status} 
                              color={getStatusColor(job.status)}
                              size="small"
                            />
                          </Box>
                          
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                            Model: {models.find(m => m.id === job.modelId)?.name || job.modelId}
                          </Typography>
                          
                          {job.status === 'running' && (
                            <Box sx={{ mb: 1 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={job.progress} 
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                              <Typography variant="caption" color="textSecondary">
                                {job.progress}% complete
                              </Typography>
                            </Box>
                          )}
                          
                          {job.confidence && (
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              Confidence: {job.confidence.toFixed(1)}%
                            </Typography>
                          )}
                          
                          <Typography variant="body2" color="textSecondary">
                            Duration: {formatDuration(job.startTime, job.endTime)}
                          </Typography>
                          
                          {job.findings.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="textSecondary">
                                Findings:
                              </Typography>
                              <List dense>
                                {job.findings.map((finding, index) => (
                                  <ListItem key={index} sx={{ py: 0 }}>
                                    <ListItemText primary={finding} />
                                  </ListItem>
                                ))}
                              </List>
                            </Box>
                          )}
                        </Box>
                        
                        <Box display="flex" flexDirection="column" gap={0.5}>
                          {job.status === 'running' && (
                            <>
                              <Tooltip title="Pause">
                                <IconButton size="small" onClick={() => pauseJob(job.id)}>
                                  <Pause />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Stop">
                                <IconButton size="small" onClick={() => stopJob(job.id)}>
                                  <Stop />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                          
                          {job.status === 'paused' && (
                            <Tooltip title="Resume">
                              <IconButton size="small" onClick={() => resumeJob(job.id)}>
                                <PlayArrow />
                              </IconButton>
                            </Tooltip>
                          )}
                          
                          {job.status === 'completed' && (
                            <>
                              <Tooltip title="View Results">
                                <IconButton 
                                  size="small" 
                                  onClick={() => {
                                    setSelectedJobId(job.id);
                                    setViewerDialog(true);
                                  }}
                                >
                                  <Visibility />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Download Report">
                                <IconButton size="small">
                                  <Download />
                                </IconButton>
                              </Tooltip>
                            </>
                          )}
                        </Box>
                      </Box>
                    </Paper>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            {/* Available Models */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Available AI Models
                  </Typography>
                  
                  <Grid container spacing={2}>
                    {models.map((model) => (
                      <Grid item xs={12} md={6} key={model.id}>
                        <Paper sx={{ p: 2 }} variant="outlined">
                          <Box display="flex" justifyContent="between" alignItems="flex-start">
                            <Box flex={1}>
                              <Box display="flex" alignItems="center" gap={1} sx={{ mb: 1 }}>
                                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                                  <Psychology />
                                </Avatar>
                                <Box>
                                  <Typography variant="subtitle2">
                                    {model.name}
                                  </Typography>
                                  <Typography variant="caption" color="textSecondary">
                                    v{model.version} • {model.type}
                                  </Typography>
                                </Box>
                                {model.isActive && (
                                  <Chip label="Active" color="success" size="small" />
                                )}
                              </Box>
                              
                              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                                {model.description}
                              </Typography>
                              
                              <Box display="flex" gap={2}>
                                <Box>
                                  <Typography variant="caption" color="textSecondary">
                                    Accuracy
                                  </Typography>
                                  <Typography variant="body2" color="success.main">
                                    {model.accuracy}%
                                  </Typography>
                                </Box>
                                <Box>
                                  <Typography variant="caption" color="textSecondary">
                                    Speed
                                  </Typography>
                                  <Typography variant="body2" color="primary.main">
                                    {model.speed}/100
                                  </Typography>
                                </Box>
                              </Box>
                            </Box>
                            
                            <IconButton size="small">
                              <Settings />
                            </IconButton>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {/* Model Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            AI Model Configuration
            <IconButton onClick={() => setConfigDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Model Performance Settings
              </Typography>
              
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>Processing Parameters</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Batch Size"
                        type="number"
                        value={batchSize}
                        onChange={(e) => setBatchSize(Number(e.target.value))}
                        inputProps={{ min: 1, max: 8 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>
                        Confidence Threshold: {(confidenceThreshold * 100).toFixed(0)}%
                      </Typography>
                      <Slider
                        value={confidenceThreshold}
                        onChange={(e, v) => setConfidenceThreshold(v as number)}
                        step={0.05}
                        min={0.5}
                        max={1.0}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography>Advanced Options</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enablePreprocessing}
                        onChange={(e) => setEnablePreprocessing(e.target.checked)}
                      />
                    }
                    label="Enable Advanced Preprocessing"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enablePostprocessing}
                        onChange={(e) => setEnablePostprocessing(e.target.checked)}
                      />
                    }
                    label="Enable Post-processing Filters"
                  />
                </AccordionDetails>
              </Accordion>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
          <Button variant="contained">Save Configuration</Button>
        </DialogActions>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Medical Study</DialogTitle>
        <DialogContent>
          <Box
            sx={{
              border: '2px dashed #ccc',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              mb: 2,
            }}
          >
            <FileUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Drop DICOM files here
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              or click to browse
            </Typography>
            <Button variant="outlined" sx={{ mt: 2 }}>
              Select Files
            </Button>
          </Box>
          
          <Alert severity="info">
            Supported formats: DICOM (.dcm), NIfTI (.nii), JPEG, PNG
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>Cancel</Button>
          <Button variant="contained">Upload</Button>
        </DialogActions>
      </Dialog>

      {/* Results Viewer Dialog */}
      <Dialog 
        open={viewerDialog} 
        onClose={() => setViewerDialog(false)} 
        maxWidth="lg" 
        fullWidth
        PaperProps={{ sx: { height: '90vh' } }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            Analysis Results
            <IconButton onClick={() => setViewerDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {selectedJobId && (
            <StudyViewer
              studyInstanceUID={analysisJobs.find(j => j.id === selectedJobId)?.studyId || ''}
              onClose={() => setViewerDialog(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </Container>
  );
};

export default AIAnalysisPage;
