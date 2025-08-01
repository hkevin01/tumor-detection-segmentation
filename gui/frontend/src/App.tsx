import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import StudiesPage from './pages/StudiesPage';
import PatientsPage from './pages/PatientsPage';
import AIAnalysisPage from './pages/AIAnalysisPage';
import FileManagementPage from './pages/FileManagementPage';
import SettingsPage from './pages/SettingsPage';

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/studies" element={<StudiesPage />} />
            <Route path="/patients" element={<PatientsPage />} />
            <Route path="/reports" element={<div>Reports Page (Coming Soon)</div>} />
            <Route path="/models" element={<AIAnalysisPage />} />
            <Route path="/files" element={<FileManagementPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
};

export default App;
