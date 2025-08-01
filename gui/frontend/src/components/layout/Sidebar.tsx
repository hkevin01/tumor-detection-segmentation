import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Assignment as StudyIcon,
  Assessment as ReportIcon,
  Settings as SettingsIcon,
  Memory as AIIcon,
  Folder as FilesIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const navigationItems = [
  { id: 'dashboard', label: 'Dashboard', path: '/', icon: DashboardIcon },
  { id: 'patients', label: 'Patients', path: '/patients', icon: PeopleIcon },
  { id: 'studies', label: 'Studies', path: '/studies', icon: StudyIcon },
  { id: 'reports', label: 'Reports', path: '/reports', icon: ReportIcon },
  { id: 'models', label: 'AI Models', path: '/models', icon: AIIcon },
  { id: 'files', label: 'Files', path: '/files', icon: FilesIcon },
  { id: 'settings', label: 'Settings', path: '/settings', icon: SettingsIcon },
];

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto' }}>
        <List>
          {navigationItems.map((item) => {
            const IconComponent = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <ListItem key={item.id} disablePadding>
                <ListItemButton
                  selected={isActive}
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                      '&:hover': {
                        backgroundColor: 'primary.dark',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'inherit',
                      },
                    },
                  }}
                >
                  <ListItemIcon>
                    <IconComponent />
                  </ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
        <Divider />
      </Box>
    </Drawer>
  );
};

export default Sidebar;
