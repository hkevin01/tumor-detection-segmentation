/*
Advanced Clinical Workflow Features for Medical GUI
=================================================

Enhanced GUI components for clinical workflows including:
- Real-time visualization
- Clinical report generation
- Advanced image analysis tools
- Treatment planning interface

Author: Tumor Detection Segmentation Team
Phase: GUI Enhancement - Task 18 Completion
*/

import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    FormControl,
    FormControlLabel,
    Grid,
    IconButton,
    InputLabel,
    LinearProgress,
    MenuItem,
    Paper,
    Select,
    Slider,
    Switch,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Tabs,
    TextField,
    Typography
} from '@mui/material';
import React, { useCallback, useEffect, useRef, useState } from 'react';

import {
    ExpandMore,
    Pause,
    PlayArrow,
    Stop
} from '@mui/icons-material';

import { OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';

// Type definitions
interface TumorMeasurement {
  id: string;
  type: 'length' | 'area' | 'volume';
  value: number;
  unit: string;
  timestamp: string;
  confidence: number;
}

interface ClinicalReport {
  id: string;
  patientId: string;
  studyId: string;
  findings: string[];
  measurements: TumorMeasurement[];
  impression: string;
  recommendations: string[];
  radiologist: string;
  timestamp: string;
  status: 'draft' | 'final' | 'amended';
}

interface ViewerSettings {
  brightness: number;
  contrast: number;
  zoom: number;
  rotation: number;
  showOverlay: boolean;
  overlayOpacity: number;
  colorMap: string;
  interpolation: string;
}

interface AnalysisJob {
  id: string;
  type: 'segmentation' | 'detection' | 'classification';
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  model: string;
  parameters: any;
  results?: any;
  startTime?: string;
  endTime?: string;
}

// Real-time 3D Visualization Component
const RealTime3DViewer: React.FC<{
  imageData: any;
  segmentationData?: any;
  settings: ViewerSettings;
  onMeasurement: (measurement: TumorMeasurement) => void;
}> = ({ imageData, segmentationData, settings, onMeasurement }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [measurementMode, setMeasurementMode] = useState<'none' | 'length' | 'area' | 'volume'>('none');

  const animationRef = useRef<number>();

  const startAnimation = useCallback(() => {
    setIsPlaying(true);
    const animate = () => {
      setCurrentSlice(prev => (prev + 1) % (imageData?.depth || 100));
      animationRef.current = requestAnimationFrame(animate);
    };
    animationRef.current = requestAnimationFrame(animate);
  }, [imageData]);

  const stopAnimation = () => {
    setIsPlaying(false);
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  };

  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return (
    <Card sx={{ height: '600px' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">3D Medical Viewer</Typography>
          <Box>
            <IconButton
              onClick={isPlaying ? stopAnimation : startAnimation}
              color="primary"
            >
              {isPlaying ? <Pause /> : <PlayArrow />}
            </IconButton>
            <IconButton onClick={stopAnimation}>
              <Stop />
            </IconButton>
          </Box>
        </Box>

        <Box height="500px" border="1px solid #ccc" borderRadius={1}>
          <Canvas camera={{ position: [0, 0, 5] }}>
            <ambientLight intensity={0.5} />
            <pointLight position={[10, 10, 10]} />

            {/* 3D Volume Rendering */}
            <mesh rotation={[settings.rotation * Math.PI / 180, 0, 0]}>
              <boxGeometry args={[2, 2, 2]} />
              <meshStandardMaterial
                color="lightblue"
                transparent
                opacity={settings.overlayOpacity}
              />
            </mesh>

            {/* Segmentation Overlay */}
            {segmentationData && settings.showOverlay && (
              <mesh position={[0, 0, 0.1]}>
                <boxGeometry args={[1.8, 1.8, 1.8]} />
                <meshStandardMaterial
                  color="red"
                  transparent
                  opacity={0.3}
                />
              </mesh>
            )}

            <OrbitControls enableZoom enablePan enableRotate />
          </Canvas>
        </Box>

        <Box mt={2}>
          <Typography variant="body2" gutterBottom>
            Slice: {currentSlice} / {imageData?.depth || 100}
          </Typography>
          <Slider
            value={currentSlice}
            min={0}
            max={imageData?.depth || 100}
            onChange={(_, value) => setCurrentSlice(value as number)}
            disabled={isPlaying}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

// Advanced Analysis Dashboard
const AnalysisDashboard: React.FC<{
  jobs: AnalysisJob[];
  onStartAnalysis: (type: string, parameters: any) => void;
  onCancelJob: (jobId: string) => void;
}> = ({ jobs, onStartAnalysis, onCancelJob }) => {
  const [analysisType, setAnalysisType] = useState('segmentation');
  const [modelSelection, setModelSelection] = useState('unetr');
  const [advancedParams, setAdvancedParams] = useState({
    roiSize: [96, 96, 96],
    batchSize: 1,
    confidence: 0.85,
    postprocessing: true,
    tta: false
  });

  const handleStartAnalysis = () => {
    onStartAnalysis(analysisType, {
      model: modelSelection,
      ...advancedParams
    });
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>AI Analysis Dashboard</Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Analysis Type</InputLabel>
              <Select
                value={analysisType}
                onChange={(e) => setAnalysisType(e.target.value)}
              >
                <MenuItem value="segmentation">Tumor Segmentation</MenuItem>
                <MenuItem value="detection">Tumor Detection</MenuItem>
                <MenuItem value="classification">Tumor Classification</MenuItem>
                <MenuItem value="cascade">Cascade Pipeline</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Model</InputLabel>
              <Select
                value={modelSelection}
                onChange={(e) => setModelSelection(e.target.value)}
              >
                <MenuItem value="unetr">UNETR (Transformer)</MenuItem>
                <MenuItem value="segresnet">SegResNet</MenuItem>
                <MenuItem value="swinunetr">Swin UNETR</MenuItem>
                <MenuItem value="unet">U-Net</MenuItem>
                <MenuItem value="cascade">Cascade Pipeline</MenuItem>
              </Select>
            </FormControl>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Advanced Parameters</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box>
                  <Typography gutterBottom>Confidence Threshold</Typography>
                  <Slider
                    value={advancedParams.confidence}
                    min={0.1}
                    max={1.0}
                    step={0.05}
                    onChange={(_, value) =>
                      setAdvancedParams(prev => ({ ...prev, confidence: value as number }))
                    }
                    valueLabelDisplay="auto"
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={advancedParams.postprocessing}
                        onChange={(e) =>
                          setAdvancedParams(prev => ({ ...prev, postprocessing: e.target.checked }))
                        }
                      />
                    }
                    label="Post-processing"
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={advancedParams.tta}
                        onChange={(e) =>
                          setAdvancedParams(prev => ({ ...prev, tta: e.target.checked }))
                        }
                      />
                    }
                    label="Test-Time Augmentation"
                  />
                </Box>
              </AccordionDetails>
            </Accordion>

            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={handleStartAnalysis}
              sx={{ mt: 2 }}
            >
              Start Analysis
            </Button>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>Active Jobs</Typography>

            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Model</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell>{job.type}</TableCell>
                      <TableCell>{job.model}</TableCell>
                      <TableCell>
                        <Chip
                          label={job.status}
                          color={
                            job.status === 'completed' ? 'success' :
                            job.status === 'failed' ? 'error' :
                            job.status === 'running' ? 'primary' : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <LinearProgress
                            variant="determinate"
                            value={job.progress}
                            sx={{ width: '80px', mr: 1 }}
                          />
                          <Typography variant="body2">{job.progress}%</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {job.status === 'running' && (
                          <IconButton
                            size="small"
                            onClick={() => onCancelJob(job.id)}
                          >
                            <Stop />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// Clinical Report Generator
const ClinicalReportGenerator: React.FC<{
  measurements: TumorMeasurement[];
  onGenerateReport: (report: Partial<ClinicalReport>) => void;
}> = ({ measurements, onGenerateReport }) => {
  const [findings, setFindings] = useState<string[]>([]);
  const [impression, setImpression] = useState('');
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [newFinding, setNewFinding] = useState('');
  const [newRecommendation, setNewRecommendation] = useState('');

  const addFinding = () => {
    if (newFinding.trim()) {
      setFindings(prev => [...prev, newFinding.trim()]);
      setNewFinding('');
    }
  };

  const addRecommendation = () => {
    if (newRecommendation.trim()) {
      setRecommendations(prev => [...prev, newRecommendation.trim()]);
      setNewRecommendation('');
    }
  };

  const generateAutoFindings = () => {
    const autoFindings = [];

    if (measurements.length > 0) {
      const volumes = measurements.filter(m => m.type === 'volume');
      if (volumes.length > 0) {
        const totalVolume = volumes.reduce((sum, m) => sum + m.value, 0);
        autoFindings.push(`Total tumor volume: ${totalVolume.toFixed(2)} cm³`);
      }

      const highConfidence = measurements.filter(m => m.confidence > 0.9);
      if (highConfidence.length > 0) {
        autoFindings.push(`${highConfidence.length} high-confidence lesions detected`);
      }
    }

    setFindings(prev => [...prev, ...autoFindings]);
  };

  const handleGenerateReport = () => {
    const report: Partial<ClinicalReport> = {
      findings,
      measurements,
      impression,
      recommendations,
      radiologist: 'AI Assistant',
      timestamp: new Date().toISOString(),
      status: 'draft'
    };

    onGenerateReport(report);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>Clinical Report Generator</Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>Findings</Typography>

            <Box display="flex" gap={1} mb={2}>
              <TextField
                fullWidth
                size="small"
                placeholder="Add finding..."
                value={newFinding}
                onChange={(e) => setNewFinding(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addFinding()}
              />
              <Button variant="outlined" onClick={addFinding}>Add</Button>
            </Box>

            <Button
              variant="outlined"
              onClick={generateAutoFindings}
              sx={{ mb: 2 }}
            >
              Auto-Generate from Measurements
            </Button>

            <Box>
              {findings.map((finding, index) => (
                <Chip
                  key={index}
                  label={finding}
                  onDelete={() => setFindings(prev => prev.filter((_, i) => i !== index))}
                  sx={{ m: 0.5 }}
                />
              ))}
            </Box>

            <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
              Measurements Summary
            </Typography>

            <TableContainer component={Paper} sx={{ maxHeight: 200 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell>Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {measurements.map((measurement) => (
                    <TableRow key={measurement.id}>
                      <TableCell>{measurement.type}</TableCell>
                      <TableCell>
                        {measurement.value.toFixed(2)} {measurement.unit}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${(measurement.confidence * 100).toFixed(1)}%`}
                          color={measurement.confidence > 0.8 ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Impression"
              value={impression}
              onChange={(e) => setImpression(e.target.value)}
              margin="normal"
            />

            <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
              Recommendations
            </Typography>

            <Box display="flex" gap={1} mb={2}>
              <TextField
                fullWidth
                size="small"
                placeholder="Add recommendation..."
                value={newRecommendation}
                onChange={(e) => setNewRecommendation(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addRecommendation()}
              />
              <Button variant="outlined" onClick={addRecommendation}>Add</Button>
            </Box>

            <Box>
              {recommendations.map((rec, index) => (
                <Chip
                  key={index}
                  label={rec}
                  onDelete={() => setRecommendations(prev => prev.filter((_, i) => i !== index))}
                  sx={{ m: 0.5 }}
                />
              ))}
            </Box>

            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={handleGenerateReport}
              sx={{ mt: 3 }}
            >
              Generate Report
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// Main Enhanced Clinical Interface
const EnhancedClinicalInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [viewerSettings, setViewerSettings] = useState<ViewerSettings>({
    brightness: 50,
    contrast: 50,
    zoom: 100,
    rotation: 0,
    showOverlay: true,
    overlayOpacity: 0.5,
    colorMap: 'gray',
    interpolation: 'linear'
  });

  const [measurements, setMeasurements] = useState<TumorMeasurement[]>([]);
  const [analysisJobs, setAnalysisJobs] = useState<AnalysisJob[]>([]);

  const handleMeasurement = (measurement: TumorMeasurement) => {
    setMeasurements(prev => [...prev, measurement]);
  };

  const handleStartAnalysis = (type: string, parameters: any) => {
    const newJob: AnalysisJob = {
      id: `job_${Date.now()}`,
      type: type as any,
      status: 'queued',
      progress: 0,
      model: parameters.model,
      parameters,
      startTime: new Date().toISOString()
    };

    setAnalysisJobs(prev => [...prev, newJob]);

    // Simulate job progress
    const interval = setInterval(() => {
      setAnalysisJobs(prev => prev.map(job =>
        job.id === newJob.id
          ? {
              ...job,
              status: job.progress >= 100 ? 'completed' : 'running',
              progress: Math.min(job.progress + 10, 100)
            }
          : job
      ));
    }, 1000);

    setTimeout(() => clearInterval(interval), 10000);
  };

  const handleCancelJob = (jobId: string) => {
    setAnalysisJobs(prev => prev.filter(job => job.id !== jobId));
  };

  const handleGenerateReport = (report: Partial<ClinicalReport>) => {
    console.log('Generated report:', report);
    // Here you would send the report to the backend
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Enhanced Clinical Interface
      </Typography>

      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
        <Tab label="3D Viewer" />
        <Tab label="AI Analysis" />
        <Tab label="Clinical Reports" />
        <Tab label="Settings" />
      </Tabs>

      <Box mt={3}>
        {activeTab === 0 && (
          <RealTime3DViewer
            imageData={{ depth: 100 }}
            segmentationData={null}
            settings={viewerSettings}
            onMeasurement={handleMeasurement}
          />
        )}

        {activeTab === 1 && (
          <AnalysisDashboard
            jobs={analysisJobs}
            onStartAnalysis={handleStartAnalysis}
            onCancelJob={handleCancelJob}
          />
        )}

        {activeTab === 2 && (
          <ClinicalReportGenerator
            measurements={measurements}
            onGenerateReport={handleGenerateReport}
          />
        )}

        {activeTab === 3 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Viewer Settings</Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>Brightness</Typography>
                  <Slider
                    value={viewerSettings.brightness}
                    onChange={(_, value) =>
                      setViewerSettings(prev => ({ ...prev, brightness: value as number }))
                    }
                    valueLabelDisplay="auto"
                  />

                  <Typography gutterBottom>Contrast</Typography>
                  <Slider
                    value={viewerSettings.contrast}
                    onChange={(_, value) =>
                      setViewerSettings(prev => ({ ...prev, contrast: value as number }))
                    }
                    valueLabelDisplay="auto"
                  />

                  <Typography gutterBottom>Overlay Opacity</Typography>
                  <Slider
                    value={viewerSettings.overlayOpacity}
                    min={0}
                    max={1}
                    step={0.1}
                    onChange={(_, value) =>
                      setViewerSettings(prev => ({ ...prev, overlayOpacity: value as number }))
                    }
                    valueLabelDisplay="auto"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={viewerSettings.showOverlay}
                        onChange={(e) =>
                          setViewerSettings(prev => ({ ...prev, showOverlay: e.target.checked }))
                        }
                      />
                    }
                    label="Show Segmentation Overlay"
                  />

                  <FormControl fullWidth margin="normal">
                    <InputLabel>Color Map</InputLabel>
                    <Select
                      value={viewerSettings.colorMap}
                      onChange={(e) =>
                        setViewerSettings(prev => ({ ...prev, colorMap: e.target.value }))
                      }
                    >
                      <MenuItem value="gray">Grayscale</MenuItem>
                      <MenuItem value="jet">Jet</MenuItem>
                      <MenuItem value="hot">Hot</MenuItem>
                      <MenuItem value="cool">Cool</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
};

export default EnhancedClinicalInterface;
