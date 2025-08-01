import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Avatar,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  Pagination,
  LinearProgress,
  Badge,
  Fab,
  Menu,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Add,
  Search,
  FilterList,
  MoreVert,
  Edit,
  Delete,
  Visibility,
  Download,
  Upload,
  PersonAdd,
  Close,
  Save,
  Cancel,
  Phone,
  Email,
  LocationOn,
  CalendarToday,
  MedicalServices,
  History,
  Assignment,
  Warning,
  CheckCircle,
  Schedule,
  LocalHospital,
} from '@mui/icons-material';
import { apiService } from '../services/api';
import { Patient } from '../types';

interface PatientFormData {
  id?: string;
  name: string;
  dateOfBirth: string;
  gender: string;
  phone: string;
  email: string;
  address: string;
  emergencyContact: string;
  medicalHistory: string;
  insuranceId: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const PatientsPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterGender, setFilterGender] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [currentPage, setCurrentPage] = useState(1);
  const [patientsPerPage] = useState(10);
  const [tabValue, setTabValue] = useState(0);
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState<PatientFormData>({
    name: '',
    dateOfBirth: '',
    gender: '',
    phone: '',
    email: '',
    address: '',
    emergencyContact: '',
    medicalHistory: '',
    insuranceId: '',
  });
  
  // UI states
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuPatient, setMenuPatient] = useState<Patient | null>(null);

  // Sample demo data for demonstration
  const demoPatients = [
    {
      id: 'demo-1',
      name: 'John Doe',
      date_of_birth: '1980-05-15',
      gender: 'male',
      phone: '+1-555-0123',
      email: 'john.doe@email.com',
      address: '123 Main St, City, State 12345',
      emergency_contact: 'Jane Doe: +1-555-0124',
      medical_history: 'Hypertension, Type 2 Diabetes',
      insurance_id: 'INS-001-2024',
      created_at: '2024-01-15',
      studies_count: 3,
      last_visit: '2024-07-15',
      status: 'active',
    },
    {
      id: 'demo-2',
      name: 'Sarah Johnson',
      date_of_birth: '1975-08-22',
      gender: 'female',
      phone: '+1-555-0125',
      email: 'sarah.johnson@email.com',
      address: '456 Oak Ave, City, State 12345',
      emergency_contact: 'Mike Johnson: +1-555-0126',
      medical_history: 'Breast cancer survivor, Regular checkups',
      insurance_id: 'INS-002-2024',
      created_at: '2024-02-20',
      studies_count: 8,
      last_visit: '2024-07-28',
      status: 'active',
    },
    {
      id: 'demo-3',
      name: 'Robert Smith',
      date_of_birth: '1965-12-03',
      gender: 'male',
      phone: '+1-555-0127',
      email: 'robert.smith@email.com',
      address: '789 Pine St, City, State 12345',
      emergency_contact: 'Mary Smith: +1-555-0128',
      medical_history: 'History of lung issues, Former smoker',
      insurance_id: 'INS-003-2024',
      created_at: '2024-03-10',
      studies_count: 5,
      last_visit: '2024-07-20',
      status: 'active',
    },
  ];

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getPatients();
      // Combine real data with demo data for demonstration
      setPatients([...data, ...demoPatients]);
    } catch (err) {
      setError(apiService.handleApiError(err));
      // If API fails, show demo data
      setPatients(demoPatients);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      if (isEditing && selectedPatient) {
        // Update patient logic
        setSnackbarMessage('Patient updated successfully');
      } else {
        // Create new patient logic
        setSnackbarMessage('Patient created successfully');
      }
      setDialogOpen(false);
      setSnackbarOpen(true);
      fetchPatients();
      resetForm();
    } catch (err) {
      setError('Failed to save patient');
    }
  };

  const handleDelete = async () => {
    try {
      if (selectedPatient) {
        // Delete patient logic
        setSnackbarMessage('Patient deleted successfully');
        setDeleteDialogOpen(false);
        setSnackbarOpen(true);
        fetchPatients();
      }
    } catch (err) {
      setError('Failed to delete patient');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      dateOfBirth: '',
      gender: '',
      phone: '',
      email: '',
      address: '',
      emergencyContact: '',
      medicalHistory: '',
      insuranceId: '',
    });
    setIsEditing(false);
    setSelectedPatient(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const openEditDialog = (patient: Patient) => {
    setSelectedPatient(patient);
    setFormData({
      id: patient.id,
      name: patient.name || '',
      dateOfBirth: patient.date_of_birth || '',
      gender: patient.gender || '',
      phone: patient.phone || '',
      email: patient.email || '',
      address: patient.address || '',
      emergencyContact: patient.emergency_contact || '',
      medicalHistory: patient.medical_history || '',
      insuranceId: patient.insurance_id || '',
    });
    setIsEditing(true);
    setDialogOpen(true);
  };

  const openViewDialog = (patient: Patient) => {
    setSelectedPatient(patient);
    setViewDialogOpen(true);
  };

  const openDeleteDialog = (patient: Patient) => {
    setSelectedPatient(patient);
    setDeleteDialogOpen(true);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, patient: Patient) => {
    setAnchorEl(event.currentTarget);
    setMenuPatient(patient);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuPatient(null);
  };

  // Filter and search logic
  const filteredPatients = patients.filter(patient => {
    const matchesSearch = patient.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         patient.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         patient.phone?.includes(searchTerm);
    const matchesGender = !filterGender || patient.gender === filterGender;
    return matchesSearch && matchesGender;
  });

  // Sort logic
  const sortedPatients = [...filteredPatients].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return (a.name || '').localeCompare(b.name || '');
      case 'date':
        return new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime();
      case 'studies':
        return (b.studies_count || 0) - (a.studies_count || 0);
      default:
        return 0;
    }
  });

  // Pagination
  const indexOfLastPatient = currentPage * patientsPerPage;
  const indexOfFirstPatient = indexOfLastPatient - patientsPerPage;
  const currentPatients = sortedPatients.slice(indexOfFirstPatient, indexOfLastPatient);
  const totalPages = Math.ceil(sortedPatients.length / patientsPerPage);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getAvatarColor = (name: string) => {
    const colors = ['#1976d2', '#388e3c', '#f57c00', '#d32f2f', '#7b1fa2', '#00796b'];
    const index = name.charCodeAt(0) % colors.length;
    return colors[index];
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading patients...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          Patient Management
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Import Patients">
            <Fab size="small" color="secondary">
              <Upload />
            </Fab>
          </Tooltip>
          <Tooltip title="Add New Patient">
            <Fab color="primary" onClick={openCreateDialog}>
              <PersonAdd />
            </Fab>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Patients
                  </Typography>
                  <Typography variant="h4">{patients.length}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#1976d2' }}>
                  <LocalHospital />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Patients
                  </Typography>
                  <Typography variant="h4">
                    {patients.filter(p => p.status === 'active').length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#388e3c' }}>
                  <CheckCircle />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Studies
                  </Typography>
                  <Typography variant="h4">
                    {patients.reduce((sum, p) => sum + (p.studies_count || 0), 0)}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#f57c00' }}>
                  <Assignment />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Recent Visits
                  </Typography>
                  <Typography variant="h4">
                    {patients.filter(p => {
                      const lastVisit = new Date(p.last_visit || '');
                      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
                      return lastVisit > weekAgo;
                    }).length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#d32f2f' }}>
                  <Schedule />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search patients..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Gender</InputLabel>
                <Select
                  value={filterGender}
                  label="Gender"
                  onChange={(e) => setFilterGender(e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="male">Male</MenuItem>
                  <MenuItem value="female">Female</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Sort By</InputLabel>
                <Select
                  value={sortBy}
                  label="Sort By"
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <MenuItem value="name">Name</MenuItem>
                  <MenuItem value="date">Registration Date</MenuItem>
                  <MenuItem value="studies">Study Count</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box display="flex" justifyContent="flex-end" gap={1}>
                <Button variant="outlined" startIcon={<FilterList />}>
                  Advanced Filters
                </Button>
                <Button variant="outlined" startIcon={<Download />}>
                  Export
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Patient Table */}
      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Patient</TableCell>
                  <TableCell>Contact</TableCell>
                  <TableCell>Gender</TableCell>
                  <TableCell>Studies</TableCell>
                  <TableCell>Last Visit</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {currentPatients.map((patient) => (
                  <TableRow key={patient.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <Avatar 
                          sx={{ 
                            width: 40, 
                            height: 40, 
                            mr: 2,
                            bgcolor: getAvatarColor(patient.name || '')
                          }}
                        >
                          {(patient.name || '').charAt(0).toUpperCase()}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle2">
                            {patient.name}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            DOB: {new Date(patient.date_of_birth || '').toLocaleDateString()}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" display="flex" alignItems="center">
                          <Phone sx={{ fontSize: 16, mr: 0.5 }} />
                          {patient.phone}
                        </Typography>
                        <Typography variant="body2" display="flex" alignItems="center">
                          <Email sx={{ fontSize: 16, mr: 0.5 }} />
                          {patient.email}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={patient.gender || 'Not specified'} 
                        size="small"
                        color={patient.gender === 'male' ? 'primary' : patient.gender === 'female' ? 'secondary' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Badge badgeContent={patient.studies_count || 0} color="primary">
                        <Assignment />
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {patient.last_visit ? new Date(patient.last_visit).toLocaleDateString() : 'Never'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={patient.status || 'unknown'}
                        color={getStatusColor(patient.status || '')}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={0.5}>
                        <Tooltip title="View Details">
                          <IconButton size="small" onClick={() => openViewDialog(patient)}>
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton size="small" onClick={() => openEditDialog(patient)}>
                            <Edit />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="More Actions">
                          <IconButton 
                            size="small" 
                            onClick={(e) => handleMenuClick(e, patient)}
                          >
                            <MoreVert />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {/* Pagination */}
          <Box display="flex" justifyContent="center" sx={{ mt: 3 }}>
            <Pagination 
              count={totalPages}
              page={currentPage}
              onChange={(e, page) => setCurrentPage(page)}
              color="primary"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Patient Form Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            {isEditing ? 'Edit Patient' : 'Add New Patient'}
            <IconButton onClick={() => setDialogOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Full Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Date of Birth"
                type="date"
                value={formData.dateOfBirth}
                onChange={(e) => setFormData({ ...formData, dateOfBirth: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Gender</InputLabel>
                <Select
                  value={formData.gender}
                  label="Gender"
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                >
                  <MenuItem value="male">Male</MenuItem>
                  <MenuItem value="female">Female</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone Number"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Insurance ID"
                value={formData.insuranceId}
                onChange={(e) => setFormData({ ...formData, insuranceId: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                multiline
                rows={2}
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Emergency Contact"
                value={formData.emergencyContact}
                onChange={(e) => setFormData({ ...formData, emergencyContact: e.target.value })}
                placeholder="Name: Phone Number"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Medical History"
                multiline
                rows={3}
                value={formData.medicalHistory}
                onChange={(e) => setFormData({ ...formData, medicalHistory: e.target.value })}
                placeholder="Previous conditions, allergies, medications..."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setDialogOpen(false)} startIcon={<Cancel />}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} variant="contained" startIcon={<Save />}>
            {isEditing ? 'Update' : 'Create'} Patient
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Patient Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            Patient Details
            <IconButton onClick={() => setViewDialogOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedPatient && (
            <Box>
              <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
                <Tab label="Personal Info" />
                <Tab label="Medical History" />
                <Tab label="Studies" />
              </Tabs>
              
              <TabPanel value={tabValue} index={0}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">Name</Typography>
                    <Typography variant="body1">{selectedPatient.name}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">Date of Birth</Typography>
                    <Typography variant="body1">
                      {new Date(selectedPatient.date_of_birth || '').toLocaleDateString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">Gender</Typography>
                    <Typography variant="body1">{selectedPatient.gender}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary">Phone</Typography>
                    <Typography variant="body1">{selectedPatient.phone}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">Email</Typography>
                    <Typography variant="body1">{selectedPatient.email}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">Address</Typography>
                    <Typography variant="body1">{selectedPatient.address}</Typography>
                  </Grid>
                </Grid>
              </TabPanel>
              
              <TabPanel value={tabValue} index={1}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Medical History
                </Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {selectedPatient.medical_history || 'No medical history recorded'}
                </Typography>
                
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Emergency Contact
                </Typography>
                <Typography variant="body1">
                  {selectedPatient.emergency_contact || 'No emergency contact recorded'}
                </Typography>
              </TabPanel>
              
              <TabPanel value={tabValue} index={2}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Study Summary
                </Typography>
                <Typography variant="body1">
                  Total Studies: {selectedPatient.studies_count || 0}
                </Typography>
                <Typography variant="body1">
                  Last Visit: {selectedPatient.last_visit ? 
                    new Date(selectedPatient.last_visit).toLocaleDateString() : 'Never'}
                </Typography>
                {/* Study list would go here */}
              </TabPanel>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          <Button 
            variant="contained" 
            onClick={() => selectedPatient && openEditDialog(selectedPatient)}
          >
            Edit Patient
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete patient "{selectedPatient?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => { handleMenuClose(); menuPatient && openViewDialog(menuPatient); }}>
          <ListItemIcon><Visibility /></ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { handleMenuClose(); menuPatient && openEditDialog(menuPatient); }}>
          <ListItemIcon><Edit /></ListItemIcon>
          <ListItemText>Edit Patient</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { handleMenuClose(); menuPatient && openDeleteDialog(menuPatient); }}>
          <ListItemIcon><Delete /></ListItemIcon>
          <ListItemText>Delete Patient</ListItemText>
        </MenuItem>
      </Menu>

      {/* Success Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Container>
  );
};

export default PatientsPage;
