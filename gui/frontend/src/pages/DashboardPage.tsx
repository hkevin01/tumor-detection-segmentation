import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Alert,
  Chip,
  Container,
  Button,
  IconButton,
  Tooltip,
  Badge,
  Avatar,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Fab,
  Snackbar,
  Divider,
} from '@mui/material';
import {
  People as PeopleIcon,
  Assignment as StudyIcon,
  CheckCircle as CompleteIcon,
  Speed as ProcessingIcon,
  TrendingUp,
  Assessment,
  LocalHospital,
  Refresh,
  Notifications,
  Upload,
  Download,
  Search,
  Settings,
  Timeline,
  Security,
  CloudUpload,
  Analytics,
  Report,
  Close,
  Warning,
  Error as ErrorIcon,
  Info,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { apiService } from '../services/api';
import { Study, Patient, HealthStatus } from '../types';

interface StatsCardProps {
  title: string;
  value: number;
  icon: React.ReactElement;
  color: string;
  trend?: string;
  details?: string;
  onClick?: () => void;
}

interface NotificationData {
  id: number;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon, color, trend, details, onClick }) => (
  <Card 
    sx={{ 
      cursor: onClick ? 'pointer' : 'default',
      transition: 'all 0.3s ease',
      '&:hover': onClick ? { transform: 'translateY(-2px)', boxShadow: 3 } : {}
    }}
    onClick={onClick}
  >
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom>
            {title}
          </Typography>
          <Typography variant="h4" component="h2" sx={{ fontWeight: 'bold' }}>
            {value}
          </Typography>
          {trend && (
            <Typography variant="caption" color="success.main">
              {trend} from last month
            </Typography>
          )}
          {details && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
              {details}
            </Typography>
          )}
        </Box>
        <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
          {icon}
        </Avatar>
      </Box>
    </CardContent>
  </Card>
);

const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [studies, setStudies] = useState<Study[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [notifications, setNotifications] = useState<NotificationData[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string>('');
  const [detailsDialog, setDetailsDialog] = useState(false);

  // Sample enhanced data for demonstration
  const chartData = [
    { name: 'Jan', studies: 65, detections: 12, patients: 45 },
    { name: 'Feb', studies: 78, detections: 15, patients: 52 },
    { name: 'Mar', studies: 90, detections: 18, patients: 58 },
    { name: 'Apr', studies: 102, detections: 22, patients: 61 },
    { name: 'May', studies: 88, detections: 19, patients: 55 },
    { name: 'Jun', studies: 95, detections: 24, patients: 63 },
  ];

  const performanceData = [
    { name: 'Detection Accuracy', value: 94.2 },
    { name: 'Processing Speed', value: 87.5 },
    { name: 'System Uptime', value: 99.8 },
    { name: 'User Satisfaction', value: 92.1 },
  ];

  const detectionTypes = [
    { name: 'Tumor', value: 45, color: '#ff6b6b' },
    { name: 'Lesion', value: 30, color: '#4ecdc4' },
    { name: 'Calcification', value: 15, color: '#45b7d1' },
    { name: 'Other', value: 10, color: '#96ceb4' },
  ];

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch health status
        const healthData = await apiService.getHealth();
        setHealth(healthData);

        // Fetch patients
        const patientsData = await apiService.getPatients();
        setPatients(patientsData);

        // Fetch studies
        const studiesData = await apiService.getStudies();
        setStudies(studiesData);

      } catch (err) {
        setError(apiService.handleApiError(err));
      } finally {
        setLoading(false);
      }
    };

    // Initialize notifications
    const initialNotifications: NotificationData[] = [
      {
        id: 1,
        type: 'success',
        title: 'Analysis Complete',
        message: 'Latest batch of studies has been processed successfully',
        timestamp: new Date(),
        read: false,
      },
      {
        id: 2,
        type: 'warning',
        title: 'High Priority Case',
        message: 'Suspicious finding detected - requires immediate review',
        timestamp: new Date(Date.now() - 300000),
        read: false,
      },
      {
        id: 3,
        type: 'info',
        title: 'System Update',
        message: 'AI model v2.1 has been deployed successfully',
        timestamp: new Date(Date.now() - 600000),
        read: true,
      },
    ];
    setNotifications(initialNotifications);

    fetchDashboardData();
  }, []);

  const completedStudies = studies.filter(study => study.status === 'completed').length;
  const processingStudies = studies.filter(study => study.status === 'processing').length;
  const studiesWithAI = studies.filter(study => study.has_ai_results).length;
  
  // Enhanced activity data combining real and demo data
  const recentActivity = [
    ...studies.slice(0, 2).map((study, index) => ({
      id: index + 1,
      patient: `Patient ${study.id}`,
      study: `${study.modality} ${study.description || 'Study'}`,
      status: study.status,
      confidence: study.has_ai_results ? Math.floor(Math.random() * 20) + 80 : 0,
      findings: study.has_ai_results ? 'AI analysis completed' : 'Pending analysis',
      timestamp: new Date(study.study_date).toLocaleString(),
      priority: study.has_ai_results ? 'high' : 'medium',
    })),
    // Add demo data for demonstration
    {
      id: 10,
      patient: 'Demo Patient A',
      study: 'CT Chest',
      status: 'completed',
      confidence: 95,
      findings: 'No abnormalities detected',
      timestamp: '2 minutes ago',
      priority: 'low',
    },
    {
      id: 11,
      patient: 'Demo Patient B',
      study: 'MRI Brain',
      status: 'processing',
      confidence: 0,
      findings: 'Analysis in progress...',
      timestamp: '5 minutes ago',
      priority: 'medium',
    },
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const [healthData, patientsData, studiesData] = await Promise.all([
        apiService.getHealth(),
        apiService.getPatients(),
        apiService.getStudies(),
      ]);
      setHealth(healthData);
      setPatients(patientsData);
      setStudies(studiesData);
      setSnackbarOpen(true);
    } catch (err) {
      setError(apiService.handleApiError(err));
    } finally {
      setRefreshing(false);
    }
  };

  const handleStatClick = (statTitle: string) => {
    setSelectedMetric(statTitle);
    setDetailsDialog(true);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#d32f2f';
      case 'medium': return '#f57c00';
      case 'low': return '#388e3c';
      default: return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CompleteIcon color="success" />;
      case 'processing': return <CircularProgress size={20} />;
      case 'pending': return <Warning color="warning" />;
      default: return <Info color="info" />;
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
        <Box sx={{ width: '100%', textAlign: 'center', py: 4 }}>
          <CircularProgress size={60} />
          <Typography sx={{ mt: 2 }}>Loading dashboard...</Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      {/* Header with Actions */}
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Clinical Dashboard
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Upload New Study">
            <Fab size="small" color="primary">
              <CloudUpload />
            </Fab>
          </Tooltip>
          <Tooltip title="Notifications">
            <IconButton onClick={() => setShowNotifications(true)}>
              <Badge badgeContent={unreadCount} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <Refresh className={refreshing ? 'rotating' : ''} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {health && (
        <Alert 
          severity={health.status === 'healthy' ? 'success' : 'error'} 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small">
              <Analytics sx={{ mr: 0.5 }} /> View Details
            </Button>
          }
        >
          System Status: {health.status}
          {health.device && ` (Device: ${health.device})`} - All systems operational
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Patients"
            value={patients.length}
            icon={<PeopleIcon fontSize="large" />}
            color="#1976d2"
            trend="+8%"
            details="Active in system"
            onClick={() => handleStatClick('Total Patients')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Studies"
            value={studies.length}
            icon={<StudyIcon fontSize="large" />}
            color="#2e7d32"
            trend="+12%"
            details="Processed this month"
            onClick={() => handleStatClick('Total Studies')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="AI Analyses"
            value={studiesWithAI}
            icon={<ProcessingIcon fontSize="large" />}
            color="#ed6c02"
            trend="+23%"
            details="Completed analyses"
            onClick={() => handleStatClick('AI Analyses')}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Detections"
            value={Math.floor(studiesWithAI * 0.3)}
            icon={<LocalHospital fontSize="large" />}
            color="#9c27b0"
            trend="+15%"
            details="Positive findings"
            onClick={() => handleStatClick('Detections')}
          />
        </Grid>
      </Grid>

      {/* Charts and Analytics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Study Volume & Analytics
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="studies" fill="#1976d2" name="Studies" />
                  <Bar dataKey="detections" fill="#d32f2f" name="Detections" />
                  <Bar dataKey="patients" fill="#2e7d32" name="Patients" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detection Types
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={detectionTypes}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {detectionTypes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Performance Metrics
              </Typography>
              <Grid container spacing={2}>
                {performanceData.map((metric, index) => (
                  <Grid item xs={12} sm={6} md={3} key={index}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h5" color="primary" sx={{ fontWeight: 'bold' }}>
                        {metric.value}%
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {metric.name}
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={metric.value} 
                        sx={{ mt: 1, height: 6, borderRadius: 3 }}
                      />
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="h6">
                  Recent AI Analyses
                </Typography>
                <Button startIcon={<Report />} variant="outlined" size="small">
                  Export Report
                </Button>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Patient</TableCell>
                      <TableCell>Study Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Findings</TableCell>
                      <TableCell>Priority</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentActivity.map((activity) => (
                      <TableRow key={activity.id} hover>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            <Avatar sx={{ width: 32, height: 32, mr: 1 }}>
                              {activity.patient.charAt(0)}
                            </Avatar>
                            {activity.patient}
                          </Box>
                        </TableCell>
                        <TableCell>{activity.study}</TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            {getStatusIcon(activity.status)}
                            <Chip
                              label={activity.status}
                              color={
                                activity.status === 'completed' ? 'success' :
                                activity.status === 'processing' ? 'warning' : 'default'
                              }
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          {activity.confidence > 0 ? (
                            <Box display="flex" alignItems="center">
                              <Typography variant="body2" sx={{ mr: 1 }}>
                                {activity.confidence}%
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={activity.confidence}
                                sx={{ width: 60, height: 6 }}
                              />
                            </Box>
                          ) : (
                            <Typography color="textSecondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {activity.findings}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={activity.priority}
                            sx={{
                              bgcolor: getPriorityColor(activity.priority),
                              color: 'white',
                            }}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Queue */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processing Queue
              </Typography>
              {processingStudies > 0 ? (
                <Box>
                  <Typography variant="h3" color="warning.main" gutterBottom>
                    {processingStudies}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Studies currently processing
                  </Typography>
                  <LinearProgress sx={{ mt: 2 }} />
                </Box>
              ) : (
                <Typography color="text.secondary">
                  No studies in queue
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button variant="outlined" startIcon={<Upload />} fullWidth>
                  Upload Study
                </Button>
                <Button variant="outlined" startIcon={<Search />} fullWidth>
                  Search Patients
                </Button>
                <Button variant="outlined" startIcon={<Report />} fullWidth>
                  Generate Report
                </Button>
                <Button variant="outlined" startIcon={<Settings />} fullWidth>
                  Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Notifications Dialog */}
      <Dialog 
        open={showNotifications} 
        onClose={() => setShowNotifications(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            Notifications
            <IconButton onClick={() => setShowNotifications(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {notifications.map((notification) => (
            <Alert 
              key={notification.id}
              severity={notification.type}
              sx={{ mb: 2 }}
              action={
                <Typography variant="caption">
                  {notification.timestamp.toLocaleTimeString()}
                </Typography>
              }
            >
              <Typography variant="subtitle2">{notification.title}</Typography>
              <Typography variant="body2">{notification.message}</Typography>
            </Alert>
          ))}
        </DialogContent>
      </Dialog>

      {/* Details Dialog */}
      <Dialog 
        open={detailsDialog} 
        onClose={() => setDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{selectedMetric} Details</DialogTitle>
        <DialogContent>
          <Typography>
            Detailed analytics and trends for {selectedMetric} would be displayed here.
            This could include historical data, breakdowns by department, and predictive analytics.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message="Dashboard data refreshed successfully"
      />
    </Container>
  );
};

export default DashboardPage;
