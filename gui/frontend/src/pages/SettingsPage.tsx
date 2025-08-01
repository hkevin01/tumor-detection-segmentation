import React, { useState } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Switch,
  FormControlLabel,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Divider,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  Badge,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Settings,
  Security,
  Notifications,
  Palette,
  Storage,
  CloudUpload,
  Psychology,
  Memory,
  Speed,
  Tune,
  Backup,
  Shield,
  Lock,
  VpnKey,
  Person,
  Group,
  AdminPanelSettings,
  ExpandMore,
  Save,
  Restore,
  Delete,
  Add,
  Edit,
  Visibility,
  VisibilityOff,
  Close,
  Warning,
  Info,
  CheckCircle,
  Schedule,
  Computer,
  Smartphone,
  Tablet,
  DesktopWindows,
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box>{children}</Box>}
  </div>
);

const SettingsPage: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [resetDialog, setResetDialog] = useState(false);
  const [backupDialog, setBackupDialog] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // General Settings
  const [generalSettings, setGeneralSettings] = useState({
    darkMode: false,
    language: 'en',
    timezone: 'UTC',
    autoSave: true,
    notifications: true,
    soundEffects: false,
    animations: true,
    compactMode: false,
  });

  // Security Settings
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorAuth: false,
    sessionTimeout: 30,
    autoLogout: true,
    passwordExpiry: 90,
    loginNotifications: true,
    deviceTracking: true,
    encryptStorage: true,
  });

  // AI/ML Settings
  const [aiSettings, setAiSettings] = useState({
    autoAnalysis: true,
    modelVersion: 'latest',
    confidenceThreshold: 0.85,
    batchSize: 1,
    gpuAcceleration: true,
    preprocessing: true,
    postprocessing: true,
    parallelProcessing: 2,
  });

  // Storage Settings
  const [storageSettings, setStorageSettings] = useState({
    autoCleanup: true,
    retentionPeriod: 365,
    compressionLevel: 'medium',
    backupFrequency: 'daily',
    cloudSync: false,
    maxFileSize: 500,
    cacheSize: 1024,
  });

  // User Management (demo data)
  const [users] = useState([
    {
      id: 1,
      name: 'Dr. John Smith',
      email: 'john.smith@hospital.com',
      role: 'Administrator',
      lastLogin: '2024-07-30 09:15:00',
      status: 'active',
      permissions: ['read', 'write', 'admin'],
    },
    {
      id: 2,
      name: 'Dr. Sarah Johnson',
      email: 'sarah.johnson@hospital.com',
      role: 'Radiologist',
      lastLogin: '2024-07-30 08:30:00',
      status: 'active',
      permissions: ['read', 'write'],
    },
    {
      id: 3,
      name: 'Tech Mike Wilson',
      email: 'mike.wilson@hospital.com',
      role: 'Technician',
      lastLogin: '2024-07-29 16:45:00',
      status: 'inactive',
      permissions: ['read'],
    },
  ]);

  // System Information
  const systemInfo = {
    version: '2.1.0',
    buildDate: '2024-07-15',
    uptime: '15 days, 6 hours',
    cpuUsage: 45,
    memoryUsage: 62,
    storageUsage: 78,
    activeUsers: 12,
    processingJobs: 3,
    apiCalls: 15420,
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const saveSettings = () => {
    // Save logic here
    setSnackbarMessage('Settings saved successfully');
    setSnackbarOpen(true);
  };

  const resetSettings = () => {
    // Reset logic here
    setResetDialog(false);
    setSnackbarMessage('Settings reset to defaults');
    setSnackbarOpen(true);
  };

  const exportBackup = () => {
    // Export logic here
    setBackupDialog(false);
    setSnackbarMessage('Backup exported successfully');
    setSnackbarOpen(true);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'Administrator': return 'error';
      case 'Radiologist': return 'primary';
      case 'Technician': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    return status === 'active' ? 'success' : 'default';
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Settings & Configuration
        </Typography>
        <Box display="flex" gap={1}>
          <Button variant="outlined" startIcon={<Backup />} onClick={() => setBackupDialog(true)}>
            Backup
          </Button>
          <Button variant="contained" startIcon={<Save />} onClick={saveSettings}>
            Save Changes
          </Button>
        </Box>
      </Box>

      {/* System Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>System Status</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {systemInfo.cpuUsage}%
                </Typography>
                <Typography variant="body2">CPU Usage</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {systemInfo.memoryUsage}%
                </Typography>
                <Typography variant="body2">Memory Usage</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  {systemInfo.storageUsage}%
                </Typography>
                <Typography variant="body2">Storage Usage</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {systemInfo.activeUsers}
                </Typography>
                <Typography variant="body2">Active Users</Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Settings Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab label="General" icon={<Settings />} />
            <Tab label="Security" icon={<Security />} />
            <Tab label="AI/ML" icon={<Psychology />} />
            <Tab label="Storage" icon={<Storage />} />
            <Tab label="Users" icon={<Group />} />
            <Tab label="System" icon={<Computer />} />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={currentTab} index={0}>
          <CardContent>
            <Typography variant="h6" gutterBottom>General Settings</Typography>
            
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Appearance & Behavior</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.darkMode}
                          onChange={(e) => setGeneralSettings(prev => ({ ...prev, darkMode: e.target.checked }))}
                        />
                      }
                      label="Dark Mode"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.animations}
                          onChange={(e) => setGeneralSettings(prev => ({ ...prev, animations: e.target.checked }))}
                        />
                      }
                      label="Enable Animations"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.compactMode}
                          onChange={(e) => setGeneralSettings(prev => ({ ...prev, compactMode: e.target.checked }))}
                        />
                      }
                      label="Compact Mode"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.soundEffects}
                          onChange={(e) => setGeneralSettings(prev => ({ ...prev, soundEffects: e.target.checked }))}
                        />
                      }
                      label="Sound Effects"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Localization</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Language</InputLabel>
                      <Select
                        value={generalSettings.language}
                        label="Language"
                        onChange={(e) => setGeneralSettings(prev => ({ ...prev, language: e.target.value }))}
                      >
                        <MenuItem value="en">English</MenuItem>
                        <MenuItem value="es">Spanish</MenuItem>
                        <MenuItem value="fr">French</MenuItem>
                        <MenuItem value="de">German</MenuItem>
                        <MenuItem value="zh">Chinese</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Timezone</InputLabel>
                      <Select
                        value={generalSettings.timezone}
                        label="Timezone"
                        onChange={(e) => setGeneralSettings(prev => ({ ...prev, timezone: e.target.value }))}
                      >
                        <MenuItem value="UTC">UTC</MenuItem>
                        <MenuItem value="EST">EST</MenuItem>
                        <MenuItem value="PST">PST</MenuItem>
                        <MenuItem value="CET">CET</MenuItem>
                        <MenuItem value="JST">JST</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Notifications</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.notifications}
                          onChange={(e) => setGeneralSettings(prev => ({ ...prev, notifications: e.target.checked }))}
                        />
                      }
                      label="Enable Notifications"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={generalSettings.autoSave}
                          onChange={(e) => setGeneralSettings(prev => ({ ...prev, autoSave: e.target.checked }))}
                        />
                      }
                      label="Auto-save Settings"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={currentTab} index={1}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Security Settings</Typography>
            
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Changes to security settings may require administrator approval and system restart.
              </Typography>
            </Alert>

            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Authentication</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.twoFactorAuth}
                          onChange={(e) => setSecuritySettings(prev => ({ ...prev, twoFactorAuth: e.target.checked }))}
                        />
                      }
                      label="Two-Factor Authentication"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.autoLogout}
                          onChange={(e) => setSecuritySettings(prev => ({ ...prev, autoLogout: e.target.checked }))}
                        />
                      }
                      label="Auto Logout"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Session Timeout (minutes)</Typography>
                    <Slider
                      value={securitySettings.sessionTimeout}
                      onChange={(e, v) => setSecuritySettings(prev => ({ ...prev, sessionTimeout: v as number }))}
                      step={5}
                      min={5}
                      max={180}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Password Expiry (days)</Typography>
                    <Slider
                      value={securitySettings.passwordExpiry}
                      onChange={(e, v) => setSecuritySettings(prev => ({ ...prev, passwordExpiry: v as number }))}
                      step={30}
                      min={30}
                      max={365}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Privacy & Monitoring</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.loginNotifications}
                          onChange={(e) => setSecuritySettings(prev => ({ ...prev, loginNotifications: e.target.checked }))}
                        />
                      }
                      label="Login Notifications"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.deviceTracking}
                          onChange={(e) => setSecuritySettings(prev => ({ ...prev, deviceTracking: e.target.checked }))}
                        />
                      }
                      label="Device Tracking"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={securitySettings.encryptStorage}
                          onChange={(e) => setSecuritySettings(prev => ({ ...prev, encryptStorage: e.target.checked }))}
                        />
                      }
                      label="Encrypt Local Storage"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </TabPanel>

        {/* AI/ML Settings */}
        <TabPanel value={currentTab} index={2}>
          <CardContent>
            <Typography variant="h6" gutterBottom>AI & Machine Learning Settings</Typography>
            
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Model Configuration</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Model Version</InputLabel>
                      <Select
                        value={aiSettings.modelVersion}
                        label="Model Version"
                        onChange={(e) => setAiSettings(prev => ({ ...prev, modelVersion: e.target.value }))}
                      >
                        <MenuItem value="latest">Latest (v2.1)</MenuItem>
                        <MenuItem value="stable">Stable (v2.0)</MenuItem>
                        <MenuItem value="legacy">Legacy (v1.8)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Confidence Threshold</Typography>
                    <Slider
                      value={aiSettings.confidenceThreshold}
                      onChange={(e, v) => setAiSettings(prev => ({ ...prev, confidenceThreshold: v as number }))}
                      step={0.05}
                      min={0.5}
                      max={1.0}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Batch Size</Typography>
                    <Slider
                      value={aiSettings.batchSize}
                      onChange={(e, v) => setAiSettings(prev => ({ ...prev, batchSize: v as number }))}
                      step={1}
                      min={1}
                      max={8}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Parallel Processing</Typography>
                    <Slider
                      value={aiSettings.parallelProcessing}
                      onChange={(e, v) => setAiSettings(prev => ({ ...prev, parallelProcessing: v as number }))}
                      step={1}
                      min={1}
                      max={4}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Processing Options</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={aiSettings.autoAnalysis}
                          onChange={(e) => setAiSettings(prev => ({ ...prev, autoAnalysis: e.target.checked }))}
                        />
                      }
                      label="Auto Analysis"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={aiSettings.gpuAcceleration}
                          onChange={(e) => setAiSettings(prev => ({ ...prev, gpuAcceleration: e.target.checked }))}
                        />
                      }
                      label="GPU Acceleration"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={aiSettings.preprocessing}
                          onChange={(e) => setAiSettings(prev => ({ ...prev, preprocessing: e.target.checked }))}
                        />
                      }
                      label="Enable Preprocessing"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={aiSettings.postprocessing}
                          onChange={(e) => setAiSettings(prev => ({ ...prev, postprocessing: e.target.checked }))}
                        />
                      }
                      label="Enable Postprocessing"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </TabPanel>

        {/* Storage Settings */}
        <TabPanel value={currentTab} index={3}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Storage & Data Management</Typography>
            
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Data Retention</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={storageSettings.autoCleanup}
                          onChange={(e) => setStorageSettings(prev => ({ ...prev, autoCleanup: e.target.checked }))}
                        />
                      }
                      label="Auto Cleanup"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={storageSettings.cloudSync}
                          onChange={(e) => setStorageSettings(prev => ({ ...prev, cloudSync: e.target.checked }))}
                        />
                      }
                      label="Cloud Sync"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Retention Period (days)</Typography>
                    <Slider
                      value={storageSettings.retentionPeriod}
                      onChange={(e, v) => setStorageSettings(prev => ({ ...prev, retentionPeriod: v as number }))}
                      step={30}
                      min={30}
                      max={1095}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Max File Size (MB)</Typography>
                    <Slider
                      value={storageSettings.maxFileSize}
                      onChange={(e, v) => setStorageSettings(prev => ({ ...prev, maxFileSize: v as number }))}
                      step={50}
                      min={50}
                      max={2000}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Compression & Backup</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Compression Level</InputLabel>
                      <Select
                        value={storageSettings.compressionLevel}
                        label="Compression Level"
                        onChange={(e) => setStorageSettings(prev => ({ ...prev, compressionLevel: e.target.value }))}
                      >
                        <MenuItem value="none">None</MenuItem>
                        <MenuItem value="low">Low</MenuItem>
                        <MenuItem value="medium">Medium</MenuItem>
                        <MenuItem value="high">High</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Backup Frequency</InputLabel>
                      <Select
                        value={storageSettings.backupFrequency}
                        label="Backup Frequency"
                        onChange={(e) => setStorageSettings(prev => ({ ...prev, backupFrequency: e.target.value }))}
                      >
                        <MenuItem value="hourly">Hourly</MenuItem>
                        <MenuItem value="daily">Daily</MenuItem>
                        <MenuItem value="weekly">Weekly</MenuItem>
                        <MenuItem value="monthly">Monthly</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography gutterBottom>Cache Size (MB)</Typography>
                    <Slider
                      value={storageSettings.cacheSize}
                      onChange={(e, v) => setStorageSettings(prev => ({ ...prev, cacheSize: v as number }))}
                      step={128}
                      min={128}
                      max={4096}
                      valueLabelDisplay="auto"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </TabPanel>

        {/* User Management */}
        <TabPanel value={currentTab} index={4}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6">User Management</Typography>
              <Button variant="contained" startIcon={<Add />}>
                Add User
              </Button>
            </Box>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>User</TableCell>
                    <TableCell>Role</TableCell>
                    <TableCell>Last Login</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <Avatar sx={{ mr: 2 }}>
                            {user.name.charAt(0)}
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle2">{user.name}</Typography>
                            <Typography variant="caption" color="textSecondary">
                              {user.email}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={user.role} 
                          color={getRoleColor(user.role)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {user.lastLogin}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={user.status} 
                          color={getStatusColor(user.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={0.5}>
                          <Tooltip title="Edit User">
                            <IconButton size="small">
                              <Edit />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View Permissions">
                            <IconButton size="small">
                              <Shield />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Reset Password">
                            <IconButton size="small">
                              <VpnKey />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </TabPanel>

        {/* System Information */}
        <TabPanel value={currentTab} index={5}>
          <CardContent>
            <Typography variant="h6" gutterBottom>System Information</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Software</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Version" secondary={systemInfo.version} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Build Date" secondary={systemInfo.buildDate} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Uptime" secondary={systemInfo.uptime} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="API Calls Today" secondary={systemInfo.apiCalls.toLocaleString()} />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>Resources</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Active Users" secondary={systemInfo.activeUsers} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Processing Jobs" secondary={systemInfo.processingJobs} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="CPU Usage" secondary={`${systemInfo.cpuUsage}%`} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Memory Usage" secondary={`${systemInfo.memoryUsage}%`} />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>System Actions</Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Button variant="outlined" startIcon={<Backup />} onClick={() => setBackupDialog(true)}>
                Create Backup
              </Button>
              <Button variant="outlined" startIcon={<Restore />}>
                Restore System
              </Button>
              <Button variant="outlined" startIcon={<Refresh />}>
                Restart Services
              </Button>
              <Button variant="outlined" color="warning" startIcon={<Warning />} onClick={() => setResetDialog(true)}>
                Reset to Defaults
              </Button>
            </Box>
          </CardContent>
        </TabPanel>
      </Card>

      {/* Reset Confirmation Dialog */}
      <Dialog open={resetDialog} onClose={() => setResetDialog(false)}>
        <DialogTitle>Reset Settings</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will reset all settings to their default values. This action cannot be undone.
          </Alert>
          <Typography>
            Are you sure you want to proceed?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialog(false)}>Cancel</Button>
          <Button onClick={resetSettings} color="warning" variant="contained">
            Reset Settings
          </Button>
        </DialogActions>
      </Dialog>

      {/* Backup Dialog */}
      <Dialog open={backupDialog} onClose={() => setBackupDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create System Backup</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Select what to include in the backup:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText primary="System Settings" secondary="All configuration settings" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText primary="User Data" secondary="User accounts and permissions" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText primary="AI Models" secondary="Trained model configurations" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <Info color="action" />
              </ListItemIcon>
              <ListItemText primary="Study Data" secondary="Patient data (excluded for privacy)" />
            </ListItem>
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBackupDialog(false)}>Cancel</Button>
          <Button onClick={exportBackup} variant="contained">
            Create Backup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Container>
  );
};

export default SettingsPage;
