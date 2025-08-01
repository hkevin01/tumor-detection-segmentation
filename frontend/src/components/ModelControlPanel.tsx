import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Memory,
  Speed,
  Tune,
  PlayArrow,
  Pause,
  Stop,
  Settings,
  Info,
  CloudDownload,
  Assessment,
  BugReport,
  History
} from '@mui/icons-material';

interface ModelConfig {
  name: string;
  architecture: string;
  parameters: number;
  device: string;
  loaded: boolean;
  training: boolean;
  performance: {
    accuracy: number;
    diceScore: number;
    hausdorffDistance: number;
    inferenceTime: number;
  };
}

interface InferenceParams {
  roiSize: number[];
  swBatchSize: number;
  overlap: number;
  mode: string;
  sigmaScale: number;
  threshold: number;
}

interface BatchJob {
  id: string;
  modelName: string;
  totalImages: number;
  processedImages: number;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: string;
  estimatedCompletion?: string;
  errorMessage?: string;
}

const ModelControlPanel: React.FC = () => {
  const [availableModels, setAvailableModels] = useState<ModelConfig[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('unet');
  const [inferenceParams, setInferenceParams] = useState<InferenceParams>({
    roiSize: [96, 96, 96],
    swBatchSize: 4,
    overlap: 0.5,
    mode: 'gaussian',
    sigmaScale: 0.125,
    threshold: 0.5
  });
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<any>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [benchmarkDialogOpen, setBenchmarkDialogOpen] = useState(false);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);
  const [autoOptimize, setAutoOptimize] = useState(false);
  
  // Mock model data
  useEffect(() => {
    const mockModels: ModelConfig[] = [
      {
        name: 'unet',
        architecture: 'UNet',
        parameters: 7832576,
        device: 'cuda:0',
        loaded: true,
        training: false,
        performance: {
          accuracy: 0.92,
          diceScore: 0.89,
          hausdorffDistance: 2.4,
          inferenceTime: 1.2
        }
      },
      {
        name: 'segresnet',
        architecture: 'SegResNet',
        parameters: 5493248,
        device: 'cuda:0',
        loaded: false,
        training: false,
        performance: {
          accuracy: 0.94,
          diceScore: 0.91,
          hausdorffDistance: 2.1,
          inferenceTime: 0.8
        }
      },
      {
        name: 'swinunetr',
        architecture: 'SwinUNETR',
        parameters: 62183424,
        device: 'cuda:0',
        loaded: false,
        training: false,
        performance: {
          accuracy: 0.96,
          diceScore: 0.93,
          hausdorffDistance: 1.8,
          inferenceTime: 2.3
        }
      }
    ];
    
    setAvailableModels(mockModels);
    
    // Mock batch jobs
    const mockBatchJobs: BatchJob[] = [
      {
        id: 'batch_001',
        modelName: 'unet',
        totalImages: 50,
        processedImages: 32,
        status: 'running',
        startTime: '2023-12-01T10:30:00Z',
        estimatedCompletion: '2023-12-01T11:15:00Z'
      },
      {
        id: 'batch_002',
        modelName: 'segresnet',
        totalImages: 25,
        processedImages: 25,
        status: 'completed',
        startTime: '2023-12-01T09:00:00Z'
      }
    ];
    
    setBatchJobs(mockBatchJobs);
  }, []);
  
  const handleModelLoad = async (modelName: string) => {
    // Simulate model loading
    setAvailableModels(prev => 
      prev.map(model => 
        model.name === modelName 
          ? { ...model, loaded: true }
          : model
      )
    );
  };
  
  const handleModelUnload = async (modelName: string) => {
    setAvailableModels(prev => 
      prev.map(model => 
        model.name === modelName 
          ? { ...model, loaded: false }
          : model
      )
    );
  };
  
  const handleParameterChange = (param: keyof InferenceParams, value: any) => {
    setInferenceParams(prev => ({
      ...prev,
      [param]: value
    }));
  };
  
  const handleRoiSizeChange = (index: number, value: number) => {
    setInferenceParams(prev => ({
      ...prev,
      roiSize: prev.roiSize.map((size, i) => i === index ? value : size)
    }));
  };
  
  const runBenchmark = async () => {
    setIsRunningBenchmark(true);
    setBenchmarkDialogOpen(true);
    
    // Simulate benchmark running
    setTimeout(() => {
      setPerformanceMetrics({
        throughput: 45.2,
        memoryUsage: 6.8,
        gpuUtilization: 87,
        averageInferenceTime: 1.2,
        peakMemoryUsage: 8.1
      });
      setIsRunningBenchmark(false);
    }, 3000);
  };
  
  const pauseBatchJob = (jobId: string) => {
    setBatchJobs(prev => 
      prev.map(job => 
        job.id === jobId 
          ? { ...job, status: 'paused' as const }
          : job
      )
    );
  };
  
  const resumeBatchJob = (jobId: string) => {
    setBatchJobs(prev => 
      prev.map(job => 
        job.id === jobId 
          ? { ...job, status: 'running' as const }
          : job
      )
    );
  };
  
  const stopBatchJob = (jobId: string) => {
    setBatchJobs(prev => prev.filter(job => job.id !== jobId));
  };
  
  const getProgressColor = (status: string) => {
    switch (status) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'paused': return 'warning';
      default: return 'primary';
    }
  };
  
  const formatNumber = (num: number) => {
    if (num >= 1e6) {
      return `${(num / 1e6).toFixed(1)}M`;
    } else if (num >= 1e3) {
      return `${(num / 1e3).toFixed(1)}K`;
    }
    return num.toString();
  };
  
  const currentModel = availableModels.find(m => m.name === selectedModel);
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Model Control Panel
      </Typography>
      
      <Grid container spacing={3}>
        {/* Model Selection and Status */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Available Models
              </Typography>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Model</TableCell>
                      <TableCell>Architecture</TableCell>
                      <TableCell>Parameters</TableCell>
                      <TableCell>Device</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Performance</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {availableModels.map((model) => (
                      <TableRow key={model.name} hover>
                        <TableCell>
                          <Typography variant="body1" fontWeight="bold">
                            {model.name.toUpperCase()}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2">
                            {model.architecture}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2">
                            {formatNumber(model.parameters)}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Chip 
                            label={model.device} 
                            size="small" 
                            color={model.device.includes('cuda') ? 'success' : 'default'}
                          />
                        </TableCell>
                        
                        <TableCell>
                          <Chip 
                            label={model.loaded ? 'Loaded' : 'Unloaded'} 
                            color={model.loaded ? 'success' : 'default'}
                            size="small"
                          />
                          {model.training && (
                            <Chip 
                              label="Training" 
                              color="warning" 
                              size="small" 
                              sx={{ ml: 1 }}
                            />
                          )}
                        </TableCell>
                        
                        <TableCell>
                          <Typography variant="body2">
                            Dice: {model.performance.diceScore.toFixed(3)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {model.performance.inferenceTime.toFixed(1)}s
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          {model.loaded ? (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => handleModelUnload(model.name)}
                            >
                              Unload
                            </Button>
                          ) : (
                            <Button
                              size="small"
                              variant="contained"
                              onClick={() => handleModelLoad(model.name)}
                            >
                              Load
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Model Configuration Panel */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Inference Configuration
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Active Model</InputLabel>
                <Select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  {availableModels.filter(m => m.loaded).map((model) => (
                    <MenuItem key={model.name} value={model.name}>
                      {model.name.toUpperCase()} - {model.architecture}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {currentModel && (
                <Box sx={{ mb: 3 }}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Model Performance:</strong><br />
                      Dice Score: {currentModel.performance.diceScore.toFixed(3)}<br />
                      Inference Time: {currentModel.performance.inferenceTime.toFixed(1)}s
                    </Typography>
                  </Alert>
                </Box>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                ROI Size
              </Typography>
              <Grid container spacing={1} sx={{ mb: 2 }}>
                {inferenceParams.roiSize.map((size, index) => (
                  <Grid item xs={4} key={index}>
                    <TextField
                      size="small"
                      type="number"
                      value={size}
                      onChange={(e) => handleRoiSizeChange(index, parseInt(e.target.value))}
                      inputProps={{ min: 32, max: 256, step: 32 }}
                    />
                  </Grid>
                ))}
              </Grid>
              
              <Typography variant="body2" gutterBottom>
                Sliding Window Batch Size
              </Typography>
              <Slider
                value={inferenceParams.swBatchSize}
                min={1}
                max={8}
                step={1}
                onChange={(_, value) => handleParameterChange('swBatchSize', value)}
                valueLabelDisplay="auto"
                sx={{ mb: 2 }}
              />
              
              <Typography variant="body2" gutterBottom>
                Overlap ({(inferenceParams.overlap * 100).toFixed(0)}%)
              </Typography>
              <Slider
                value={inferenceParams.overlap}
                min={0}
                max={0.9}
                step={0.1}
                onChange={(_, value) => handleParameterChange('overlap', value)}
                valueLabelDisplay="auto"
                sx={{ mb: 2 }}
              />
              
              <Typography variant="body2" gutterBottom>
                Threshold ({(inferenceParams.threshold * 100).toFixed(0)}%)
              </Typography>
              <Slider
                value={inferenceParams.threshold}
                min={0.1}
                max={0.9}
                step={0.05}
                onChange={(_, value) => handleParameterChange('threshold', value)}
                valueLabelDisplay="auto"
                sx={{ mb: 2 }}
              />
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Inference Mode</InputLabel>
                <Select
                  value={inferenceParams.mode}
                  onChange={(e) => handleParameterChange('mode', e.target.value)}
                >
                  <MenuItem value="gaussian">Gaussian</MenuItem>
                  <MenuItem value="constant">Constant</MenuItem>
                </Select>
              </FormControl>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={autoOptimize}
                    onChange={(e) => setAutoOptimize(e.target.checked)}
                  />
                }
                label="Auto-optimize parameters"
              />
              
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  onClick={() => setConfigDialogOpen(true)}
                >
                  Advanced
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Assessment />}
                  onClick={runBenchmark}
                >
                  Benchmark
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Batch Processing Queue */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Batch Processing Queue
              </Typography>
              
              {batchJobs.length === 0 ? (
                <Typography color="text.secondary">
                  No active batch jobs
                </Typography>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Job ID</TableCell>
                        <TableCell>Model</TableCell>
                        <TableCell>Progress</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Start Time</TableCell>
                        <TableCell>ETA</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {batchJobs.map((job) => (
                        <TableRow key={job.id}>
                          <TableCell>
                            <Typography variant="body2" fontFamily="monospace">
                              {job.id}
                            </Typography>
                          </TableCell>
                          
                          <TableCell>
                            <Chip label={job.modelName.toUpperCase()} size="small" />
                          </TableCell>
                          
                          <TableCell>
                            <Box sx={{ width: '100%' }}>
                              <LinearProgress
                                variant="determinate"
                                value={(job.processedImages / job.totalImages) * 100}
                                color={getProgressColor(job.status) as any}
                                sx={{ mb: 0.5 }}
                              />
                              <Typography variant="body2" color="text.secondary">
                                {job.processedImages} / {job.totalImages} images
                              </Typography>
                            </Box>
                          </TableCell>
                          
                          <TableCell>
                            <Chip 
                              label={job.status} 
                              color={getProgressColor(job.status) as any}
                              size="small"
                            />
                          </TableCell>
                          
                          <TableCell>
                            <Typography variant="body2">
                              {new Date(job.startTime).toLocaleTimeString()}
                            </Typography>
                          </TableCell>
                          
                          <TableCell>
                            <Typography variant="body2">
                              {job.estimatedCompletion 
                                ? new Date(job.estimatedCompletion).toLocaleTimeString()
                                : '-'
                              }
                            </Typography>
                          </TableCell>
                          
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {job.status === 'running' ? (
                                <Tooltip title="Pause">
                                  <IconButton 
                                    size="small" 
                                    onClick={() => pauseBatchJob(job.id)}
                                  >
                                    <Pause />
                                  </IconButton>
                                </Tooltip>
                              ) : job.status === 'paused' ? (
                                <Tooltip title="Resume">
                                  <IconButton 
                                    size="small" 
                                    onClick={() => resumeBatchJob(job.id)}
                                  >
                                    <PlayArrow />
                                  </IconButton>
                                </Tooltip>
                              ) : null}
                              
                              <Tooltip title="Stop">
                                <IconButton 
                                  size="small" 
                                  onClick={() => stopBatchJob(job.id)}
                                >
                                  <Stop />
                                </IconButton>
                              </Tooltip>
                              
                              <Tooltip title="Details">
                                <IconButton size="small">
                                  <Info />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Performance Metrics */}
        {performanceMetrics && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Metrics
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Memory sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                      <Typography variant="h6">
                        {performanceMetrics.memoryUsage.toFixed(1)} GB
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Memory Usage
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Speed sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                      <Typography variant="h6">
                        {performanceMetrics.throughput.toFixed(1)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Images/hour
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Tune sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                      <Typography variant="h6">
                        {performanceMetrics.gpuUtilization}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        GPU Utilization
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Assessment sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
                      <Typography variant="h6">
                        {performanceMetrics.averageInferenceTime.toFixed(1)}s
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg. Inference Time
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
      
      {/* Advanced Configuration Dialog */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Advanced Model Configuration</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Sigma Scale"
                type="number"
                value={inferenceParams.sigmaScale}
                onChange={(e) => handleParameterChange('sigmaScale', parseFloat(e.target.value))}
                inputProps={{ min: 0.01, max: 1.0, step: 0.01 }}
                sx={{ mb: 2 }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Use mixed precision"
              />
              
              <FormControlLabel
                control={<Switch />}
                label="Enable caching"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Maximum memory usage (GB)"
                type="number"
                defaultValue={8}
                inputProps={{ min: 1, max: 32 }}
                sx={{ mb: 2 }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Enable progress callbacks"
              />
              
              <FormControlLabel
                control={<Switch />}
                label="Save intermediate results"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Apply Changes</Button>
        </DialogActions>
      </Dialog>
      
      {/* Benchmark Dialog */}
      <Dialog open={benchmarkDialogOpen} onClose={() => setBenchmarkDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Model Benchmark</DialogTitle>
        <DialogContent>
          {isRunningBenchmark ? (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography>Running benchmark tests...</Typography>
              <Typography variant="body2" color="text.secondary">
                This may take a few minutes
              </Typography>
            </Box>
          ) : performanceMetrics ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                Benchmark Results
              </Typography>
              
              <Typography variant="body1" gutterBottom>
                <strong>Throughput:</strong> {performanceMetrics.throughput.toFixed(1)} images/hour
              </Typography>
              
              <Typography variant="body1" gutterBottom>
                <strong>Memory Usage:</strong> {performanceMetrics.memoryUsage.toFixed(1)} GB
              </Typography>
              
              <Typography variant="body1" gutterBottom>
                <strong>Peak Memory:</strong> {performanceMetrics.peakMemoryUsage.toFixed(1)} GB
              </Typography>
              
              <Typography variant="body1" gutterBottom>
                <strong>GPU Utilization:</strong> {performanceMetrics.gpuUtilization}%
              </Typography>
              
              <Typography variant="body1">
                <strong>Average Inference Time:</strong> {performanceMetrics.averageInferenceTime.toFixed(1)}s
              </Typography>
            </Box>
          ) : (
            <Typography>Click "Run Benchmark" to test model performance</Typography>
          )}
        </DialogContent>
        <DialogActions>
          {!isRunningBenchmark && (
            <>
              <Button onClick={() => setBenchmarkDialogOpen(false)}>Close</Button>
              <Button variant="contained" onClick={runBenchmark}>
                Run Benchmark
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ModelControlPanel;
