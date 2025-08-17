import {
    CheckCircle,
    LocalHospital,
    Psychology,
    Report,
    Schedule,
    Warning
} from '@mui/icons-material';
import {
    Box,
    Button,
    Card,
    CardContent,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    FormControlLabel,
    Grid,
    InputLabel,
    LinearProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    MenuItem,
    Paper,
    Select,
    Switch,
    Typography
} from '@mui/material';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import DicomViewer from './DicomViewer';

interface StudyData {
  study_instance_uid: string;
  patient_id: string;
  patient_name: string;
  study_date: string;
  study_description: string;
  series_count: number;
  instance_count: number;
  modality: string[];
  ai_analysis_status: 'pending' | 'processing' | 'completed' | 'failed';
  findings?: {
    tumor_count: number;
    max_confidence: number;
    recommendations: string[];
    risk_level: 'low' | 'medium' | 'high';
  };
}

interface StudyViewerProps {
  studyInstanceUID: string;
  onClose: () => void;
}

const StudyViewer: React.FC<StudyViewerProps> = ({ studyInstanceUID, onClose }) => {
  const [studyData, setStudyData] = useState<StudyData | null>(null);
  const [imageIds, setImageIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiProcessing, setAiProcessing] = useState(false);
  const [selectedSeries, setSelectedSeries] = useState<string | null>(null);
  const [tumorDetections, setTumorDetections] = useState<any[]>([]);
  const [showTumorOverlay, setShowTumorOverlay] = useState(true);
  const [overlayAlpha, setOverlayAlpha] = useState<number>(0.4);
  const [overlayCmap, setOverlayCmap] = useState<string>('jet');
  const [reportDialogOpen, setReportDialogOpen] = useState(false);

  // Load study data
  useEffect(() => {
    const loadStudyData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/studies/${studyInstanceUID}`);
        setStudyData(response.data);

        // Load first series by default
        if (response.data.series && response.data.series.length > 0) {
          const firstSeries = response.data.series[0];
          setSelectedSeries(firstSeries.series_instance_uid);
          await loadSeriesImages(firstSeries.series_instance_uid);
        }
      } catch (error) {
        console.error('Failed to load study data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStudyData();
  }, [studyInstanceUID]);

  // Load DICOM images for a series
  const loadSeriesImages = async (seriesInstanceUID: string) => {
    try {
      const response = await axios.get(`/api/series/${seriesInstanceUID}/images`);
      const images = response.data.images || [];

      // Convert to Cornerstone image IDs format
      const cornerstoneImageIds = images.map((image: any) =>
        `wadouri:${image.image_url || `/api/images/${image.sop_instance_uid}`}`
      );

      setImageIds(cornerstoneImageIds);

      // Load AI predictions if available
      await loadAIPredictions(seriesInstanceUID);
    } catch (error) {
      console.error('Failed to load series images:', error);
    }
  };

  // Load AI predictions for the series
  const loadAIPredictions = async (seriesInstanceUID: string) => {
    try {
      const response = await axios.get(`/api/ai/predictions/${seriesInstanceUID}`);
      setTumorDetections(response.data.detections || []);
    } catch (error) {
      console.error('Failed to load AI predictions:', error);
    }
  };

  // Trigger AI analysis
  const runAIAnalysis = async () => {
    if (!selectedSeries) return;

    try {
      setAiProcessing(true);
      const response = await axios.post('/api/ai/analyze', {
        series_instance_uid: selectedSeries,
        model_name: 'tumor_detection_v1'
      });

      if (response.data.task_id) {
        // Poll for results
        pollAIResults(response.data.task_id);
      }
    } catch (error) {
      console.error('Failed to start AI analysis:', error);
      setAiProcessing(false);
    }
  };

  // Poll AI analysis results
  const pollAIResults = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/ai/results/${taskId}`);

        if (response.data.status === 'completed') {
          setTumorDetections(response.data.detections || []);
          setAiProcessing(false);
          clearInterval(pollInterval);

          // Update study data with AI results
          if (studyData) {
            setStudyData({
              ...studyData,
              ai_analysis_status: 'completed',
              findings: response.data.findings
            });
          }
        } else if (response.data.status === 'failed') {
          setAiProcessing(false);
          clearInterval(pollInterval);
          console.error('AI analysis failed:', response.data.error);
        }
      } catch (error) {
        console.error('Failed to poll AI results:', error);
        setAiProcessing(false);
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  // Generate report
  const generateReport = async () => {
    try {
      const response = await axios.post('/api/reports/generate', {
        study_instance_uid: studyInstanceUID,
        include_ai_findings: true
      });

      // Open report in new window or download
      window.open(`/api/reports/${response.data.report_id}/pdf`, '_blank');
    } catch (error) {
      console.error('Failed to generate report:', error);
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'processing': return <Schedule color="warning" />;
      case 'failed': return <Warning color="error" />;
      default: return <Schedule color="disabled" />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Typography>Loading study...</Typography>
      </Box>
    );
  }

  if (!studyData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Typography color="error">Failed to load study data</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 1 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={8}>
            <Typography variant="h6">
              {studyData.patient_name} - {studyData.study_description}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Study Date: {studyData.study_date} | Patient ID: {studyData.patient_id}
            </Typography>
          </Grid>
          <Grid item xs={4} sx={{ textAlign: 'right' }}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button variant="outlined" size="small" onClick={() => setReportDialogOpen(true)}>
                <Report sx={{ mr: 1 }} />
                Report
              </Button>
              <Button variant="outlined" size="small" onClick={onClose}>
                Close
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={1} sx={{ flex: 1 }}>
        {/* Left sidebar - Study info and AI results */}
        <Grid item xs={3}>
          <Paper sx={{ height: '100%', p: 2, overflow: 'auto' }}>
            {/* Study Information */}
            <Typography variant="h6" gutterBottom>
              Study Information
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <LocalHospital />
                </ListItemIcon>
                <ListItemText
                  primary="Modality"
                  secondary={studyData.modality.join(', ')}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Series Count"
                  secondary={studyData.series_count}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Instance Count"
                  secondary={studyData.instance_count}
                />
              </ListItem>
            </List>

            <Divider sx={{ my: 2 }} />

            {/* AI Analysis */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ flex: 1 }}>
                AI Analysis
              </Typography>
              {getStatusIcon(studyData.ai_analysis_status)}
            </Box>

            {aiProcessing && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Processing...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            {studyData.ai_analysis_status === 'completed' && studyData.findings ? (
              <Card variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    AI Findings
                  </Typography>
                  <Box sx={{ mb: 1 }}>
                    <Chip
                      label={`Risk: ${studyData.findings.risk_level.toUpperCase()}`}
                      color={getRiskLevelColor(studyData.findings.risk_level) as any}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2">
                    Tumors detected: {studyData.findings.tumor_count}
                  </Typography>
                  <Typography variant="body2">
                    Max confidence: {Math.round(studyData.findings.max_confidence * 100)}%
                  </Typography>
                  {studyData.findings.recommendations.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" display="block" gutterBottom>
                        Recommendations:
                      </Typography>
                      {studyData.findings.recommendations.map((rec, index) => (
                        <Typography key={index} variant="caption" display="block">
                          • {rec}
                        </Typography>
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Button
                variant="contained"
                fullWidth
                startIcon={<Psychology />}
                onClick={runAIAnalysis}
                disabled={aiProcessing || !selectedSeries}
              >
                Run AI Analysis
              </Button>
            )}

            {/* Tumor Detections List */}
            {tumorDetections.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Detections ({tumorDetections.length})
                </Typography>
                <List dense>
                  {tumorDetections.slice(0, 5).map((detection, index) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={`${detection.type || 'Tumor'}`}
                        secondary={`Confidence: ${Math.round((detection.confidence || 0) * 100)}%`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}

            {/* Overlay controls */}
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Overlay Controls
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={<Switch checked={showTumorOverlay} onChange={(e) => setShowTumorOverlay(e.target.checked)} size="small" />}
                label="Show Tumor Overlay"
              />
              <Typography variant="caption">Opacity: {Math.round(overlayAlpha * 100)}%</Typography>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={overlayAlpha}
                onChange={(e) => setOverlayAlpha(parseFloat(e.target.value))}
              />
              <FormControl size="small" fullWidth>
                <InputLabel>Colormap</InputLabel>
                <Select
                  label="Colormap"
                  value={overlayCmap}
                  onChange={(e) => setOverlayCmap(e.target.value)}
                >
                  {['jet', 'viridis', 'plasma', 'magma', 'inferno', 'turbo'].map((cm) => (
                    <MenuItem key={cm} value={cm}>{cm}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          </Paper>
        </Grid>

        {/* Main viewer */}
        <Grid item xs={9}>
          <DicomViewer
            studyInstanceUID={studyInstanceUID}
            seriesInstanceUID={selectedSeries || undefined}
            imageIds={imageIds}
            showTumorOverlay={showTumorOverlay}
            overlayAlpha={overlayAlpha}
            overlayCmap={overlayCmap}
            tumorDetections={tumorDetections}
            onImageLoad={(data) => {
              console.log('Images loaded:', data);
            }}
            onMeasurement={(measurement) => {
              console.log('Measurement created:', measurement);
            }}
          />
        </Grid>
      </Grid>

      {/* Report Dialog */}
      <Dialog open={reportDialogOpen} onClose={() => setReportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Report</DialogTitle>
        <DialogContent>
          <Typography>
            Generate a comprehensive report including clinical findings and AI analysis results.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialogOpen(false)}>Cancel</Button>
          <Button onClick={generateReport} variant="contained">
            Generate PDF Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudyViewer;
