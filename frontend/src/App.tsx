import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { 
  Box, 
  AppBar, 
  Toolbar, 
  Typography, 
  Container, 
  Tabs, 
  Tab,
  Badge,
  IconButton,
  Menu,
  MenuItem,
  Chip
} from '@mui/material';
import {
  ViewInAr,
  People,
  Settings,
  NotificationsNone,
  AccountCircle
} from '@mui/icons-material';

import DicomViewer from './components/DicomViewer';
import PatientManagement from './components/PatientManagement';
import ModelControlPanel from './components/ModelControlPanel';

// Create a dark theme for medical imaging
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          border: '1px solid #333',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          minWidth: 120,
        },
      },
    },
  },
});

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`main-tabpanel-${index}`}
      aria-labelledby={`main-tab-${index}`}
    >
      {value === index && children}
    </div>
  );
};

const App: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <AppBar position="static" elevation={1}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Medical Imaging AI - Tumor Detection & Segmentation
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip 
                label="MONAI-Powered" 
                variant="outlined" 
                size="small" 
                color="primary"
              />
              
              <Badge badgeContent={2} color="error">
                <IconButton color="inherit">
                  <NotificationsNone />
                </IconButton>
              </Badge>
              
              <IconButton
                color="inherit"
                onClick={handleProfileMenuOpen}
              >
                <AccountCircle />
              </IconButton>
            </Box>
          </Toolbar>
          
          {/* Main Navigation Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="medical imaging tabs"
              textColor="inherit"
              indicatorColor="secondary"
            >
              <Tab 
                label="DICOM Viewer" 
                icon={<ViewInAr />} 
                iconPosition="start"
                id="main-tab-0"
                aria-controls="main-tabpanel-0"
              />
              <Tab 
                label="Patient Management" 
                icon={<People />} 
                iconPosition="start"
                id="main-tab-1"
                aria-controls="main-tabpanel-1"
              />
              <Tab 
                label="Model Control" 
                icon={<Settings />} 
                iconPosition="start"
                id="main-tab-2"
                aria-controls="main-tabpanel-2"
              />
            </Tabs>
          </Box>
        </AppBar>
        
        {/* Main Content Area */}
        <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
          <TabPanel value={tabValue} index={0}>
            <DicomViewer />
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <PatientManagement />
          </TabPanel>
          
          <TabPanel value={tabValue} index={2}>
            <ModelControlPanel />
          </TabPanel>
        </Box>
        
        {/* Profile Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleProfileMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          <MenuItem onClick={handleProfileMenuClose}>
            <Typography variant="body2" color="text.secondary">
              Dr. Sarah Johnson
            </Typography>
          </MenuItem>
          <MenuItem onClick={handleProfileMenuClose}>Profile Settings</MenuItem>
          <MenuItem onClick={handleProfileMenuClose}>Preferences</MenuItem>
          <MenuItem onClick={handleProfileMenuClose}>Sign Out</MenuItem>
        </Menu>
      </Box>
    </ThemeProvider>
  );
};

export default App;
