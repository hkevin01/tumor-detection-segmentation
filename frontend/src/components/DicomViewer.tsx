import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Paper,
  IconButton,
  Tooltip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Upload,
  Refresh,
  ZoomIn,
  ZoomOut,
  PanTool,
  CenterFocusStrong,
  Visibility,
  VisibilityOff,
  Download,
  Compare,
  Timeline,
  Settings,
  PlayArrow,
  Pause
} from '@mui/icons-material';

// DICOM viewer interfaces
interface DicomMetadata {
  patientId: string;
  studyDate: string;
  modality: string;
  seriesDescription: string;
  spacing: number[];
  dimensions: number[];
  windowCenter: number;
  windowWidth: number;
}

interface TumorPrediction {
  segmentationMask: number[][][];
  confidenceScore: number;
  tumorVolume: number;
  boundingBox: {
    min: number[];
    max: number[];
  };
  modelUsed: string;
  inferenceTime: string;
}

interface ViewportSettings {
  windowCenter: number;
  windowWidth: number;
  zoom: number;
  pan: { x: number; y: number };
  orientation: 'axial' | 'sagittal' | 'coronal';
  slice: number;
}

const DicomViewer: React.FC = () => {
  // Core state management
  const [dicomData, setDicomData] = useState<any>(null);
  const [metadata, setMetadata] = useState<DicomMetadata | null>(null);
  const [prediction, setPrediction] = useState<TumorPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Viewport state
  const [viewportSettings, setViewportSettings] = useState<ViewportSettings>({
    windowCenter: 40,
    windowWidth: 400,
    zoom: 1.0,
    pan: { x: 0, y: 0 },
    orientation: 'axial',
    slice: 0
  });
  
  // UI state
  const [showSegmentation, setShowSegmentation] = useState(true);
  const [segmentationOpacity, setSegmentationOpacity] = useState(0.5);
  const [selectedModel, setSelectedModel] = useState('unet');
  const [isPlaying, setIsPlaying] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  
  // Refs for canvas rendering
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  
  // File upload handler
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const file = files[0];
      const formData = new FormData();
      formData.append('dicom_file', file);
      
      // Upload DICOM file to backend
      const response = await fetch('/api/dicom/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error('Failed to upload DICOM file');
      }
      
      const result = await response.json();
      setDicomData(result.dicom_data);
      setMetadata(result.metadata);
      
      // Update viewport settings based on DICOM metadata
      setViewportSettings(prev => ({
        ...prev,
        windowCenter: result.metadata.windowCenter || 40,
        windowWidth: result.metadata.windowWidth || 400,
        slice: Math.floor(result.metadata.dimensions[2] / 2)
      }));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load DICOM file');
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Tumor prediction handler
  const handleTumorPrediction = useCallback(async () => {
    if (!dicomData) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/ai/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dicom_id: dicomData.id,
          model_name: selectedModel,
          inference_params: {
            roi_size: [96, 96, 96],
            sw_batch_size: 4,
            overlap: 0.5
          }
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to run tumor prediction');
      }
      
      const result = await response.json();
      setPrediction(result);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setIsLoading(false);
    }
  }, [dicomData, selectedModel]);
  
  // Window/Level adjustment
  const handleWindowLevelChange = useCallback((type: 'center' | 'width', value: number) => {
    setViewportSettings(prev => ({
      ...prev,
      [type === 'center' ? 'windowCenter' : 'windowWidth']: value
    }));
  }, []);
  
  // Slice navigation
  const handleSliceChange = useCallback((slice: number) => {
    if (!metadata) return;
    
    const maxSlice = metadata.dimensions[2] - 1;
    const clampedSlice = Math.max(0, Math.min(slice, maxSlice));
    
    setViewportSettings(prev => ({
      ...prev,
      slice: clampedSlice
    }));
  }, [metadata]);
  
  // Auto-play through slices
  useEffect(() => {
    if (!isPlaying || !metadata) return;
    
    const interval = setInterval(() => {
      setViewportSettings(prev => {
        const nextSlice = (prev.slice + 1) % metadata.dimensions[2];
        return { ...prev, slice: nextSlice };
      });
    }, 200);
    
    return () => clearInterval(interval);
  }, [isPlaying, metadata]);
  
  // Canvas rendering effect
  useEffect(() => {
    if (!dicomData || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Render DICOM slice
    const { windowCenter, windowWidth, slice, orientation } = viewportSettings;
    
    // This would contain the actual DICOM rendering logic
    // For now, showing placeholder rendering
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Add slice number indicator
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '16px Arial';
    ctx.fillText(`${orientation.toUpperCase()} - Slice ${slice + 1}`, 10, 30);
    
  }, [dicomData, viewportSettings]);
  
  // Segmentation overlay rendering
  useEffect(() => {
    if (!prediction || !showSegmentation || !overlayCanvasRef.current) return;
    
    const canvas = overlayCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Render segmentation mask with opacity
    ctx.fillStyle = `rgba(255, 0, 0, ${segmentationOpacity})`;
    
    // This would contain the actual segmentation rendering logic
    // For demonstration, showing a mock tumor region
    ctx.fillRect(50, 50, 100, 80);
    
  }, [prediction, showSegmentation, segmentationOpacity, viewportSettings.slice]);
  
  return (
    <Box sx={{ p: 3, height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header with controls */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h5" component="h1">
              Medical Imaging Viewer
            </Typography>
            {metadata && (
              <Typography variant="body2" color="text.secondary">
                Patient: {metadata.patientId} | Study: {metadata.studyDate} | {metadata.modality}
              </Typography>
            )}
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                component="label"
                startIcon={<Upload />}
                disabled={isLoading}
              >
                Load DICOM
                <input
                  type="file"
                  hidden
                  accept=".dcm,.dicom"
                  onChange={handleFileUpload}
                />
              </Button>
              
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={handleTumorPrediction}
                disabled={!dicomData || isLoading}
              >
                Run AI Analysis
              </Button>
              
              <IconButton onClick={() => setSettingsOpen(true)}>
                <Settings />
              </IconButton>
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={2} sx={{ flexGrow: 1 }}>
        {/* Main viewer panel */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%', position: 'relative' }}>
            <CardContent sx={{ height: '100%', p: 1 }}>
              {isLoading && (
                <Box sx={{ 
                  position: 'absolute', 
                  top: '50%', 
                  left: '50%', 
                  transform: 'translate(-50%, -50%)',
                  zIndex: 10
                }}>
                  <CircularProgress />
                </Box>
              )}
              
              {/* DICOM Canvas */}
              <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
                <canvas
                  ref={canvasRef}
                  width={512}
                  height={512}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    backgroundColor: '#000000'
                  }}
                />
                
                {/* Segmentation Overlay */}
                <canvas
                  ref={overlayCanvasRef}
                  width={512}
                  height={512}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    pointerEvents: 'none'
                  }}
                />
              </Box>
              
              {/* Slice Navigation */}
              {metadata && (
                <Box sx={{ position: 'absolute', bottom: 20, left: 20, right: 20 }}>
                  <Paper sx={{ p: 2, backgroundColor: 'rgba(255,255,255,0.9)' }}>
                    <Grid container alignItems="center" spacing={2}>
                      <Grid item>
                        <IconButton 
                          onClick={() => setIsPlaying(!isPlaying)}
                          disabled={!dicomData}
                        >
                          {isPlaying ? <Pause /> : <PlayArrow />}
                        </IconButton>
                      </Grid>
                      
                      <Grid item xs>
                        <Slider
                          value={viewportSettings.slice}
                          min={0}
                          max={metadata.dimensions[2] - 1}
                          onChange={(_, value) => handleSliceChange(value as number)}
                          valueLabelDisplay="auto"
                          valueLabelFormat={(value) => `Slice ${value + 1}`}
                        />
                      </Grid>
                      
                      <Grid item>
                        <Typography variant="body2">
                          {viewportSettings.slice + 1} / {metadata.dimensions[2]}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Control Panel */}
        <Grid item xs={12} md={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>
            
            {/* Window/Level Controls */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Display Settings
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2">Window Center</Typography>
                    <Slider
                      value={viewportSettings.windowCenter}
                      min={-1000}
                      max={1000}
                      onChange={(_, value) => handleWindowLevelChange('center', value as number)}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Typography variant="body2">Window Width</Typography>
                    <Slider
                      value={viewportSettings.windowWidth}
                      min={1}
                      max={2000}
                      onChange={(_, value) => handleWindowLevelChange('width', value as number)}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                </Grid>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={showSegmentation}
                      onChange={(e) => setShowSegmentation(e.target.checked)}
                    />
                  }
                  label="Show Segmentation"
                />
                
                {showSegmentation && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2">Overlay Opacity</Typography>
                    <Slider
                      value={segmentationOpacity}
                      min={0}
                      max={1}
                      step={0.1}
                      onChange={(_, value) => setSegmentationOpacity(value as number)}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
            
            {/* AI Model Controls */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Analysis
                </Typography>
                
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Model</InputLabel>
                  <Select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                  >
                    <MenuItem value="unet">UNet</MenuItem>
                    <MenuItem value="segresnet">SegResNet</MenuItem>
                    <MenuItem value="swinunetr">SwinUNETR</MenuItem>
                  </Select>
                </FormControl>
                
                {prediction && (
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Analysis Results:
                    </Typography>
                    
                    <Chip
                      label={`Confidence: ${(prediction.confidenceScore * 100).toFixed(1)}%`}
                      color={prediction.confidenceScore > 0.8 ? 'success' : 'warning'}
                      sx={{ mr: 1, mb: 1 }}
                    />
                    
                    <Chip
                      label={`Volume: ${prediction.tumorVolume.toFixed(1)} mm³`}
                      color="primary"
                      sx={{ mr: 1, mb: 1 }}
                    />
                    
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      Model: {prediction.modelUsed}
                    </Typography>
                    
                    <Typography variant="body2">
                      Time: {new Date(prediction.inferenceTime).toLocaleTimeString()}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
            
            {/* Patient Information */}
            {metadata && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Study Information
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Patient ID:</strong> {metadata.patientId}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Study Date:</strong> {metadata.studyDate}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Modality:</strong> {metadata.modality}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Series:</strong> {metadata.seriesDescription}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Dimensions:</strong> {metadata.dimensions.join(' × ')}
                  </Typography>
                  
                  <Typography variant="body2">
                    <strong>Spacing:</strong> {metadata.spacing.map(s => s.toFixed(2)).join(' × ')} mm
                  </Typography>
                </CardContent>
              </Card>
            )}
            
            {/* Export Options */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Export & Tools
                </Typography>
                
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Download />}
                  disabled={!prediction}
                  sx={{ mb: 1 }}
                >
                  Export Segmentation
                </Button>
                
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Compare />}
                  disabled={!prediction}
                  sx={{ mb: 1 }}
                >
                  Compare Studies
                </Button>
                
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Timeline />}
                  disabled={!metadata}
                >
                  Longitudinal Analysis
                </Button>
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>
      
      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Viewer Settings</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Orientation</InputLabel>
            <Select
              value={viewportSettings.orientation}
              onChange={(e) => setViewportSettings(prev => ({
                ...prev,
                orientation: e.target.value as 'axial' | 'sagittal' | 'coronal'
              }))}
            >
              <MenuItem value="axial">Axial</MenuItem>
              <MenuItem value="sagittal">Sagittal</MenuItem>
              <MenuItem value="coronal">Coronal</MenuItem>
            </Select>
          </FormControl>
          
          <Typography variant="body2" gutterBottom>
            Zoom Level
          </Typography>
          <Slider
            value={viewportSettings.zoom}
            min={0.1}
            max={5.0}
            step={0.1}
            onChange={(_, value) => setViewportSettings(prev => ({
              ...prev,
              zoom: value as number
            }))}
            valueLabelDisplay="auto"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DicomViewer;
