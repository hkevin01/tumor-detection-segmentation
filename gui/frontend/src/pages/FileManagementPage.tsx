import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Paper,
  LinearProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Fab,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Badge,
  Avatar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Snackbar,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  CloudUpload,
  FileUpload,
  Delete,
  Download,
  Visibility,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Info,
  Search,
  FilterList,
  Refresh,
  FolderOpen,
  InsertDriveFile,
  Image,
  Description,
  DataUsage,
  Schedule,
  Storage,
  Security,
  ExpandMore,
  Close,
  PlayArrow,
  Pause,
  Stop,
  MoreVert,
  Share,
  Archive,
  Unarchive,
  Star,
  StarBorder,
} from '@mui/icons-material';

interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  uploadedAt: Date;
  processedAt?: Date;
  studyId?: string;
  seriesCount?: number;
  imageCount?: number;
  modality?: string;
  patientName?: string;
  studyDate?: string;
  errors?: string[];
  metadata?: Record<string, any>;
}

interface FileFilter {
  status: string;
  type: string;
  dateRange: string;
  searchTerm: string;
}

const FileManagementPage: React.FC = () => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [filter, setFilter] = useState<FileFilter>({
    status: '',
    type: '',
    dateRange: '',
    searchTerm: '',
  });
  const [viewDialog, setViewDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadFile | null>(null);
  const [batchDialog, setBatchDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Demo files for demonstration
  const demoFiles: UploadFile[] = [
    {
      id: 'file-001',
      name: 'CT_Chest_Patient_A.dcm',
      size: 52428800, // 50MB
      type: 'application/dicom',
      status: 'completed',
      progress: 100,
      uploadedAt: new Date(Date.now() - 3600000), // 1 hour ago
      processedAt: new Date(Date.now() - 3300000),
      studyId: 'study-001',
      seriesCount: 3,
      imageCount: 128,
      modality: 'CT',
      patientName: 'John Doe',
      studyDate: '2024-07-30',
      metadata: {
        institutionName: 'City General Hospital',
        manufacturer: 'GE Healthcare',
        sliceThickness: 2.5,
      },
    },
    {
      id: 'file-002',
      name: 'MRI_Brain_Patient_B.zip',
      size: 104857600, // 100MB
      type: 'application/zip',
      status: 'processing',
      progress: 67,
      uploadedAt: new Date(Date.now() - 1800000), // 30 min ago
      seriesCount: 5,
      imageCount: 256,
      modality: 'MRI',
      patientName: 'Jane Smith',
      studyDate: '2024-07-30',
    },
    {
      id: 'file-003',
      name: 'CT_Abdomen_Patient_C.dcm',
      size: 78643200, // 75MB
      type: 'application/dicom',
      status: 'error',
      progress: 45,
      uploadedAt: new Date(Date.now() - 600000), // 10 min ago
      errors: ['Invalid DICOM format', 'Missing required metadata'],
      patientName: 'Robert Johnson',
    },
    {
      id: 'file-004',
      name: 'PET_Scan_Patient_D.nii',
      size: 26214400, // 25MB
      type: 'application/octet-stream',
      status: 'uploading',
      progress: 23,
      uploadedAt: new Date(),
      modality: 'PT',
      patientName: 'Maria Garcia',
    },
  ];

  useEffect(() => {
    setFiles(demoFiles);
  }, []);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFiles = (fileList: File[]) => {
    setUploading(true);
    
    fileList.forEach((file) => {
      const newFile: UploadFile = {
        id: `file-${Date.now()}-${Math.random()}`,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        progress: 0,
        uploadedAt: new Date(),
      };
      
      setFiles(prev => [newFile, ...prev]);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setFiles(prev => 
          prev.map(f => 
            f.id === newFile.id && f.progress < 100
              ? { ...f, progress: Math.min(f.progress + 10, 100) }
              : f
          )
        );
      }, 500);
      
      // Complete upload simulation
      setTimeout(() => {
        clearInterval(progressInterval);
        setFiles(prev => 
          prev.map(f => 
            f.id === newFile.id
              ? { 
                  ...f, 
                  status: 'completed',
                  progress: 100,
                  processedAt: new Date(),
                  studyId: `study-${Date.now()}`,
                  seriesCount: Math.floor(Math.random() * 5) + 1,
                  imageCount: Math.floor(Math.random() * 200) + 50,
                }
              : f
          )
        );
        setSnackbarMessage(`File "${file.name}" uploaded successfully`);
        setSnackbarOpen(true);
      }, 5000);
    });
    
    setUploading(false);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const deleteFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    setSnackbarMessage('File deleted successfully');
    setSnackbarOpen(true);
  };

  const retryUpload = (fileId: string) => {
    setFiles(prev => 
      prev.map(f => 
        f.id === fileId ? { ...f, status: 'uploading', progress: 0, errors: undefined } : f
      )
    );
  };

  const pauseUpload = (fileId: string) => {
    setFiles(prev => 
      prev.map(f => 
        f.id === fileId ? { ...f, status: 'error' } : f
      )
    );
  };

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(filter.searchTerm.toLowerCase()) ||
                         file.patientName?.toLowerCase().includes(filter.searchTerm.toLowerCase());
    const matchesStatus = !filter.status || file.status === filter.status;
    const matchesType = !filter.type || file.type.includes(filter.type);
    
    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'uploading': return 'primary';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle color="success" />;
      case 'processing': return <Schedule color="warning" />;
      case 'uploading': return <CloudUpload color="primary" />;
      case 'error': return <ErrorIcon color="error" />;
      default: return <Info />;
    }
  };

  const getFileIcon = (type: string) => {
    if (type.includes('dicom')) return <DataUsage color="primary" />;
    if (type.includes('image')) return <Image color="secondary" />;
    if (type.includes('zip')) return <Archive color="warning" />;
    return <InsertDriveFile />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const totalFiles = files.length;
  const completedFiles = files.filter(f => f.status === 'completed').length;
  const uploadingFiles = files.filter(f => f.status === 'uploading').length;
  const errorFiles = files.filter(f => f.status === 'error').length;
  const totalSize = files.reduce((sum, f) => sum + f.size, 0);

  const uploadSteps = [
    'File Validation',
    'DICOM Processing',
    'Metadata Extraction',
    'Study Creation',
    'Quality Check',
  ];

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1">
          File Management
        </Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Batch Operations">
            <Fab size="small" color="secondary" onClick={() => setBatchDialog(true)}>
              <MoreVert />
            </Fab>
          </Tooltip>
          <Tooltip title="Refresh">
            <Fab size="small" color="primary">
              <Refresh />
            </Fab>
          </Tooltip>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>Total Files</Typography>
                  <Typography variant="h4">{totalFiles}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#1976d2' }}>
                  <Storage />
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
                  <Typography color="textSecondary" gutterBottom>Completed</Typography>
                  <Typography variant="h4">{completedFiles}</Typography>
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
                  <Typography color="textSecondary" gutterBottom>Uploading</Typography>
                  <Typography variant="h4">{uploadingFiles}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#f57c00' }}>
                  <CloudUpload />
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
                  <Typography color="textSecondary" gutterBottom>Total Size</Typography>
                  <Typography variant="h4">{formatFileSize(totalSize)}</Typography>
                </Box>
                <Avatar sx={{ bgcolor: '#d32f2f' }}>
                  <DataUsage />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Upload Area */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Upload Files</Typography>
              
              {/* Drag & Drop Zone */}
              <Paper
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                sx={{
                  p: 4,
                  textAlign: 'center',
                  border: '2px dashed',
                  borderColor: dragActive ? 'primary.main' : 'grey.300',
                  bgcolor: dragActive ? 'primary.50' : 'background.paper',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  mb: 2,
                }}
              >
                <FileUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  {dragActive ? 'Drop files here' : 'Drag & drop files'}
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  or click to browse
                </Typography>
                
                <input
                  type="file"
                  multiple
                  accept=".dcm,.nii,.zip,.jpg,.png"
                  onChange={handleFileInput}
                  style={{ display: 'none' }}
                  id="file-input"
                />
                <label htmlFor="file-input">
                  <Button variant="outlined" component="span" disabled={uploading}>
                    Select Files
                  </Button>
                </label>
              </Paper>
              
              <Alert severity="info" sx={{ mb: 2 }}>
                Supported: DICOM (.dcm), NIfTI (.nii), ZIP archives, JPEG, PNG
              </Alert>

              {/* Upload Progress for Active Uploads */}
              {uploadingFiles > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Upload Progress
                  </Typography>
                  {files
                    .filter(f => f.status === 'uploading')
                    .map(file => (
                      <Box key={file.id} sx={{ mb: 1 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="caption" noWrap sx={{ maxWidth: 200 }}>
                            {file.name}
                          </Typography>
                          <Typography variant="caption">
                            {file.progress}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={file.progress}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                    ))
                  }
                </Box>
              )}

              {/* Quick Actions */}
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>Quick Actions</Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button variant="outlined" size="small" startIcon={<FolderOpen />}>
                  Browse Studies
                </Button>
                <Button variant="outlined" size="small" startIcon={<Archive />}>
                  Create Archive
                </Button>
                <Button variant="outlined" size="small" startIcon={<Download />}>
                  Export Data
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* File List */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
                <Typography variant="h6">Files & Studies</Typography>
                <Button startIcon={<FilterList />} size="small">
                  Advanced Filters
                </Button>
              </Box>

              {/* Filters */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} md={3}>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder="Search files..."
                    value={filter.searchTerm}
                    onChange={(e) => setFilter(prev => ({ ...prev, searchTerm: e.target.value }))}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Search />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControl size="small" fullWidth>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={filter.status}
                      label="Status"
                      onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
                    >
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="completed">Completed</MenuItem>
                      <MenuItem value="uploading">Uploading</MenuItem>
                      <MenuItem value="processing">Processing</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <FormControl size="small" fullWidth>
                    <InputLabel>Type</InputLabel>
                    <Select
                      value={filter.type}
                      label="Type"
                      onChange={(e) => setFilter(prev => ({ ...prev, type: e.target.value }))}
                    >
                      <MenuItem value="">All</MenuItem>
                      <MenuItem value="dicom">DICOM</MenuItem>
                      <MenuItem value="image">Images</MenuItem>
                      <MenuItem value="zip">Archives</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Box display="flex" gap={1}>
                    <Button 
                      variant="outlined" 
                      size="small"
                      onClick={() => setFilter({ status: '', type: '', dateRange: '', searchTerm: '' })}
                    >
                      Clear
                    </Button>
                    <Button variant="outlined" size="small" startIcon={<Download />}>
                      Export
                    </Button>
                  </Box>
                </Grid>
              </Grid>

              {/* File Table */}
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>File</TableCell>
                      <TableCell>Patient</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Size</TableCell>
                      <TableCell>Upload Time</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredFiles.map((file) => (
                      <TableRow key={file.id} hover>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            {getFileIcon(file.type)}
                            <Box sx={{ ml: 1 }}>
                              <Typography variant="subtitle2">{file.name}</Typography>
                              {file.modality && (
                                <Typography variant="caption" color="textSecondary">
                                  {file.modality} • {file.imageCount} images
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {file.patientName || 'Unknown'}
                          </Typography>
                          {file.studyDate && (
                            <Typography variant="caption" color="textSecondary">
                              {file.studyDate}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            {getStatusIcon(file.status)}
                            <Chip
                              label={file.status}
                              color={getStatusColor(file.status)}
                              size="small"
                            />
                            {file.status === 'uploading' && (
                              <Typography variant="caption">
                                {file.progress}%
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>{formatFileSize(file.size)}</TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {file.uploadedAt.toLocaleTimeString()}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            {file.uploadedAt.toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={0.5}>
                            {file.status === 'completed' && (
                              <>
                                <Tooltip title="View Details">
                                  <IconButton 
                                    size="small" 
                                    onClick={() => {
                                      setSelectedFile(file);
                                      setViewDialog(true);
                                    }}
                                  >
                                    <Visibility />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title="Download">
                                  <IconButton size="small">
                                    <Download />
                                  </IconButton>
                                </Tooltip>
                              </>
                            )}
                            
                            {file.status === 'uploading' && (
                              <Tooltip title="Pause">
                                <IconButton size="small" onClick={() => pauseUpload(file.id)}>
                                  <Pause />
                                </IconButton>
                              </Tooltip>
                            )}
                            
                            {file.status === 'error' && (
                              <Tooltip title="Retry">
                                <IconButton size="small" onClick={() => retryUpload(file.id)}>
                                  <Refresh />
                                </IconButton>
                              </Tooltip>
                            )}
                            
                            <Tooltip title="Delete">
                              <IconButton 
                                size="small" 
                                onClick={() => {
                                  setSelectedFile(file);
                                  setDeleteDialog(true);
                                }}
                              >
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {filteredFiles.length === 0 && (
                <Box textAlign="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    No files match the current filters
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* File Details Dialog */}
      <Dialog open={viewDialog} onClose={() => setViewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            File Details
            <IconButton onClick={() => setViewDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedFile && (
            <Box>
              {/* Processing Steps */}
              {selectedFile.status === 'processing' && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>Processing Progress</Typography>
                  <Stepper activeStep={Math.floor((selectedFile.progress / 100) * uploadSteps.length)} alternativeLabel>
                    {uploadSteps.map((label) => (
                      <Step key={label}>
                        <StepLabel>{label}</StepLabel>
                      </Step>
                    ))}
                  </Stepper>
                </Box>
              )}

              {/* File Information */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Typography variant="h6">File Information</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="textSecondary">Name</Typography>
                      <Typography variant="body1">{selectedFile.name}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="textSecondary">Size</Typography>
                      <Typography variant="body1">{formatFileSize(selectedFile.size)}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="textSecondary">Type</Typography>
                      <Typography variant="body1">{selectedFile.type}</Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="textSecondary">Uploaded</Typography>
                      <Typography variant="body1">
                        {selectedFile.uploadedAt.toLocaleString()}
                      </Typography>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Study Information */}
              {selectedFile.studyId && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="h6">Study Information</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary">Patient Name</Typography>
                        <Typography variant="body1">{selectedFile.patientName}</Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary">Study Date</Typography>
                        <Typography variant="body1">{selectedFile.studyDate}</Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary">Modality</Typography>
                        <Typography variant="body1">{selectedFile.modality}</Typography>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="textSecondary">Images</Typography>
                        <Typography variant="body1">{selectedFile.imageCount}</Typography>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Metadata */}
              {selectedFile.metadata && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="h6">Metadata</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {Object.entries(selectedFile.metadata).map(([key, value]) => (
                        <Grid item xs={12} md={6} key={key}>
                          <Typography variant="body2" color="textSecondary">{key}</Typography>
                          <Typography variant="body1">{String(value)}</Typography>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Errors */}
              {selectedFile.errors && selectedFile.errors.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="h6" gutterBottom color="error">
                    Errors
                  </Typography>
                  <List>
                    {selectedFile.errors.map((error, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <ErrorIcon color="error" />
                        </ListItemIcon>
                        <ListItemText primary={error} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialog(false)}>Close</Button>
          {selectedFile?.status === 'completed' && (
            <Button variant="contained" startIcon={<Download />}>
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedFile?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button 
            onClick={() => {
              if (selectedFile) deleteFile(selectedFile.id);
              setDeleteDialog(false);
            }}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Batch Operations Dialog */}
      <Dialog open={batchDialog} onClose={() => setBatchDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Batch Operations</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Select files to perform batch operations:
          </Typography>
          <Box display="flex" flexDirection="column" gap={1} sx={{ mt: 2 }}>
            <Button variant="outlined" startIcon={<Download />}>
              Download Selected
            </Button>
            <Button variant="outlined" startIcon={<Archive />}>
              Create Archive
            </Button>
            <Button variant="outlined" startIcon={<PlayArrow />}>
              Batch Process
            </Button>
            <Button variant="outlined" color="error" startIcon={<Delete />}>
              Delete Selected
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

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

export default FileManagementPage;
