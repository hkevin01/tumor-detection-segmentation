import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Divider,
  Alert,
  Tabs,
  Tab,
  Avatar,
  LinearProgress
} from '@mui/material';
import {
  Person,
  CalendarToday,
  Visibility,
  Compare,
  Assignment,
  TrendingUp,
  LocalHospital,
  Science,
  Timeline as TimelineIcon,
  Download,
  Print,
  Share
} from '@mui/icons-material';

interface PatientData {
  id: string;
  name: string;
  age: number;
  gender: string;
  dateOfBirth: string;
  medicalRecordNumber: string;
  primaryPhysician: string;
  diagnosis: string;
  lastVisit: string;
}

interface StudyData {
  id: string;
  studyDate: string;
  modality: string;
  seriesDescription: string;
  bodyPart: string;
  status: 'completed' | 'pending' | 'in-progress';
  findings: string;
  tumorVolume?: number;
  confidenceScore?: number;
}

interface TreatmentEvent {
  id: string;
  date: string;
  type: 'surgery' | 'chemotherapy' | 'radiation' | 'imaging' | 'consultation';
  description: string;
  outcome?: string;
  physician: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`patient-tabpanel-${index}`}
      aria-labelledby={`patient-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const PatientManagement: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<PatientData | null>(null);
  const [patientStudies, setPatientStudies] = useState<StudyData[]>([]);
  const [treatmentHistory, setTreatmentHistory] = useState<TreatmentEvent[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [compareDialogOpen, setCompareDialogOpen] = useState(false);
  const [selectedStudies, setSelectedStudies] = useState<string[]>([]);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  
  // Mock patient data
  const mockPatient: PatientData = {
    id: 'PT001',
    name: 'John Smith',
    age: 58,
    gender: 'Male',
    dateOfBirth: '1965-03-15',
    medicalRecordNumber: 'MRN123456',
    primaryPhysician: 'Dr. Sarah Johnson',
    diagnosis: 'Glioblastoma Multiforme (GBM)',
    lastVisit: '2023-12-01'
  };
  
  // Mock studies data
  const mockStudies: StudyData[] = [
    {
      id: 'ST001',
      studyDate: '2023-12-01',
      modality: 'MRI',
      seriesDescription: 'T1W Post-Contrast',
      bodyPart: 'Brain',
      status: 'completed',
      findings: 'Enhancing mass in right frontal lobe, 3.2 cm diameter',
      tumorVolume: 1245.6,
      confidenceScore: 0.92
    },
    {
      id: 'ST002',
      studyDate: '2023-09-15',
      modality: 'MRI',
      seriesDescription: 'T1W Post-Contrast',
      bodyPart: 'Brain',
      status: 'completed',
      findings: 'Enhancing mass in right frontal lobe, 2.8 cm diameter',
      tumorVolume: 1156.8,
      confidenceScore: 0.89
    },
    {
      id: 'ST003',
      studyDate: '2023-06-20',
      modality: 'MRI',
      seriesDescription: 'T1W Post-Contrast',
      bodyPart: 'Brain',
      status: 'completed',
      findings: 'Initial enhancing mass in right frontal lobe, 2.1 cm diameter',
      tumorVolume: 892.3,
      confidenceScore: 0.85
    }
  ];
  
  // Mock treatment history
  const mockTreatmentHistory: TreatmentEvent[] = [
    {
      id: 'TR001',
      date: '2023-07-15',
      type: 'surgery',
      description: 'Craniotomy with gross total resection',
      outcome: 'Successful resection, 95% tumor removal',
      physician: 'Dr. Michael Chen'
    },
    {
      id: 'TR002',
      date: '2023-08-01',
      type: 'radiation',
      description: 'Intensity-modulated radiation therapy (IMRT)',
      outcome: 'Completed 30 fractions, well tolerated',
      physician: 'Dr. Emily Rodriguez'
    },
    {
      id: 'TR003',
      date: '2023-08-15',
      type: 'chemotherapy',
      description: 'Temozolomide therapy initiated',
      outcome: 'Ongoing treatment, good tolerance',
      physician: 'Dr. Sarah Johnson'
    }
  ];
  
  useEffect(() => {
    // Simulate loading patient data
    setSelectedPatient(mockPatient);
    setPatientStudies(mockStudies);
    setTreatmentHistory(mockTreatmentHistory);
  }, []);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleStudySelect = (studyId: string) => {
    setSelectedStudies(prev => 
      prev.includes(studyId) 
        ? prev.filter(id => id !== studyId)
        : [...prev, studyId]
    );
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in-progress': return 'warning';
      case 'pending': return 'default';
      default: return 'default';
    }
  };
  
  const getTreatmentIcon = (type: string) => {
    switch (type) {
      case 'surgery': return <LocalHospital />;
      case 'chemotherapy': return <Science />;
      case 'radiation': return <TrendingUp />;
      case 'imaging': return <Visibility />;
      case 'consultation': return <Assignment />;
      default: return <Assignment />;
    }
  };
  
  const getTreatmentColor = (type: string) => {
    switch (type) {
      case 'surgery': return 'error';
      case 'chemotherapy': return 'primary';
      case 'radiation': return 'warning';
      case 'imaging': return 'info';
      case 'consultation': return 'default';
      default: return 'default';
    }
  };
  
  const calculateVolumeChange = () => {
    if (patientStudies.length < 2) return null;
    
    const latest = patientStudies[0];
    const previous = patientStudies[1];
    
    if (!latest.tumorVolume || !previous.tumorVolume) return null;
    
    const change = latest.tumorVolume - previous.tumorVolume;
    const percentChange = (change / previous.tumorVolume) * 100;
    
    return {
      absolute: change,
      percent: percentChange,
      trend: change > 0 ? 'increase' : change < 0 ? 'decrease' : 'stable'
    };
  };
  
  const volumeChange = calculateVolumeChange();
  
  if (!selectedPatient) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading patient data...</Typography>
      </Box>
    );
  }
  
  return (
    <Box sx={{ p: 3 }}>
      {/* Patient Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item>
              <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}>
                <Person sx={{ fontSize: 40 }} />
              </Avatar>
            </Grid>
            
            <Grid item xs>
              <Typography variant="h4" gutterBottom>
                {selectedPatient.name}
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    MRN: {selectedPatient.medicalRecordNumber}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Age: {selectedPatient.age} | {selectedPatient.gender}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Primary Physician
                  </Typography>
                  <Typography variant="body1">
                    {selectedPatient.primaryPhysician}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Diagnosis
                  </Typography>
                  <Typography variant="body1">
                    {selectedPatient.diagnosis}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="body2" color="text.secondary">
                    Last Visit
                  </Typography>
                  <Typography variant="body1">
                    {new Date(selectedPatient.lastVisit).toLocaleDateString()}
                  </Typography>
                </Grid>
              </Grid>
            </Grid>
            
            <Grid item>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => setReportDialogOpen(true)}
                >
                  Generate Report
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Compare />}
                  onClick={() => setCompareDialogOpen(true)}
                  disabled={selectedStudies.length < 2}
                >
                  Compare Studies
                </Button>
              </Box>
            </Grid>
          </Grid>
          
          {/* Volume Change Alert */}
          {volumeChange && (
            <Alert 
              severity={volumeChange.trend === 'decrease' ? 'success' : 'warning'} 
              sx={{ mt: 2 }}
            >
              <Typography variant="body2">
                <strong>Tumor Volume Change:</strong> {volumeChange.absolute > 0 ? '+' : ''}
                {volumeChange.absolute.toFixed(1)} mm³ ({volumeChange.percent > 0 ? '+' : ''}
                {volumeChange.percent.toFixed(1)}%) compared to previous study
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>
      
      {/* Navigation Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="patient management tabs">
          <Tab label="Studies" icon={<Visibility />} />
          <Tab label="Treatment Timeline" icon={<TimelineIcon />} />
          <Tab label="Analysis Results" icon={<Science />} />
          <Tab label="Reports" icon={<Assignment />} />
        </Tabs>
      </Paper>
      
      {/* Studies Tab */}
      <TabPanel value={tabValue} index={0}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Imaging Studies
            </Typography>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      {/* Checkbox for selection */}
                    </TableCell>
                    <TableCell>Study Date</TableCell>
                    <TableCell>Modality</TableCell>
                    <TableCell>Series</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Tumor Volume</TableCell>
                    <TableCell>AI Confidence</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {patientStudies.map((study) => (
                    <TableRow key={study.id} hover>
                      <TableCell padding="checkbox">
                        <input
                          type="checkbox"
                          checked={selectedStudies.includes(study.id)}
                          onChange={() => handleStudySelect(study.id)}
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(study.studyDate).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip label={study.modality} size="small" />
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {study.seriesDescription}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip 
                          label={study.status} 
                          color={getStatusColor(study.status) as any}
                          size="small" 
                        />
                      </TableCell>
                      
                      <TableCell>
                        {study.tumorVolume && (
                          <Typography variant="body2">
                            {study.tumorVolume.toFixed(1)} mm³
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        {study.confidenceScore && (
                          <Typography variant="body2">
                            {(study.confidenceScore * 100).toFixed(1)}%
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <IconButton size="small">
                          <Visibility />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>
      
      {/* Treatment Timeline Tab */}
      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Treatment Timeline
            </Typography>
            
            <Timeline>
              {treatmentHistory.map((event, index) => (
                <TimelineItem key={event.id}>
                  <TimelineOppositeContent color="text.secondary">
                    {new Date(event.date).toLocaleDateString()}
                  </TimelineOppositeContent>
                  
                  <TimelineSeparator>
                    <TimelineDot color={getTreatmentColor(event.type) as any}>
                      {getTreatmentIcon(event.type)}
                    </TimelineDot>
                    {index < treatmentHistory.length - 1 && <TimelineConnector />}
                  </TimelineSeparator>
                  
                  <TimelineContent>
                    <Paper elevation={1} sx={{ p: 2 }}>
                      <Typography variant="h6" component="h3">
                        {event.description}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">
                        {event.physician}
                      </Typography>
                      
                      {event.outcome && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          <strong>Outcome:</strong> {event.outcome}
                        </Typography>
                      )}
                    </Paper>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </CardContent>
        </Card>
      </TabPanel>
      
      {/* Analysis Results Tab */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Tumor Volume Progression
                </Typography>
                
                {/* This would contain a chart showing volume over time */}
                <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography color="text.secondary">
                    Volume progression chart would be displayed here
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Response Assessment
                </Typography>
                
                {volumeChange && (
                  <Box>
                    <Typography variant="body1" gutterBottom>
                      <strong>Current Assessment:</strong> {
                        volumeChange.percent < -30 ? 'Partial Response' :
                        volumeChange.percent < -10 ? 'Minor Response' :
                        volumeChange.percent < 20 ? 'Stable Disease' :
                        'Progressive Disease'
                      }
                    </Typography>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Based on RECIST 1.1 criteria
                    </Typography>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="body2">
                      Volume change: {volumeChange.absolute > 0 ? '+' : ''}
                      {volumeChange.absolute.toFixed(1)} mm³
                    </Typography>
                    
                    <Typography variant="body2">
                      Percentage change: {volumeChange.percent > 0 ? '+' : ''}
                      {volumeChange.percent.toFixed(1)}%
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
      
      {/* Reports Tab */}
      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Clinical Reports
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Download />}
                  sx={{ mb: 1 }}
                >
                  Radiology Report
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Print />}
                  sx={{ mb: 1 }}
                >
                  Treatment Summary
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<Share />}
                  sx={{ mb: 1 }}
                >
                  Progress Report
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </TabPanel>
      
      {/* Compare Studies Dialog */}
      <Dialog open={compareDialogOpen} onClose={() => setCompareDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Compare Studies</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Select studies to compare for longitudinal analysis.
          </Typography>
          
          {selectedStudies.length >= 2 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {selectedStudies.length} studies selected for comparison
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" disabled={selectedStudies.length < 2}>
            Compare Selected
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Report Generation Dialog */}
      <Dialog open={reportDialogOpen} onClose={() => setReportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Clinical Report</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Report Type</InputLabel>
            <Select defaultValue="comprehensive">
              <MenuItem value="comprehensive">Comprehensive Report</MenuItem>
              <MenuItem value="progress">Progress Report</MenuItem>
              <MenuItem value="comparison">Study Comparison</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Additional Notes"
            placeholder="Add any additional clinical notes or observations..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Generate Report</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PatientManagement;
