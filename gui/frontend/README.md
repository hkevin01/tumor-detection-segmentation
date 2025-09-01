# Frontend Development Setup Guide

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm or yarn package manager
- Backend server running (see backend setup)

### Installation & Setup

1. **Navigate to Frontend Directory**
   ```bash
   cd gui/frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm start
   ```

4. **Open in Browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🏗️ Project Structure

```
src/
├── components/          # Reusable UI components
│   └── layout/         # Layout components (Header, Sidebar)
├── pages/              # Main application pages
├── services/           # API communication layer
├── types/              # TypeScript type definitions
├── App.tsx             # Main application component
├── index.tsx           # Application entry point
└── index.css           # Global styles
```

## 🎯 Key Features Implemented

### ✅ Core Infrastructure
- **React with TypeScript** - Type-safe development
- **Material-UI (MUI)** - Professional medical interface components
- **React Router** - Client-side navigation
- **Axios** - HTTP client for API communication
- **Responsive Layout** - Professional sidebar and header

### ✅ Clinical Interface Components
- **Dashboard** - System overview with health status and statistics
- **Studies Management** - DICOM upload, study listing, AI processing
- **Professional Medical UI** - Color-coded status indicators, progress tracking
- **Error Handling** - Comprehensive error boundaries and user feedback

### ✅ API Integration
- **Complete API Service Layer** - All backend endpoints integrated
- **File Upload** - DICOM file handling with progress tracking
- **Real-time Updates** - Study status and AI processing monitoring
- **Error Management** - User-friendly error messages and recovery

## 📋 Available Scripts

```bash
# Development
npm start          # Start development server
npm run build      # Build for production
npm test           # Run test suite
npm run eject      # Eject from Create React App (not recommended)

# Linting and Formatting
npm run lint       # Check code quality
npm run format     # Format code
```

## 🔧 Configuration

### Environment Variables
Create `.env` file in frontend directory (or rely on docker env):
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
```

### Proxy Configuration
The `package.json` includes proxy setup for development:
```json
"proxy": "http://localhost:8000"
```

## 🎨 UI Components Available

### Layout Components
- **Header** - Application title, notifications, user menu
- **Sidebar** - Navigation menu with icons
- **Layout** - Main application wrapper

### Page Components
- **Dashboard** - System overview and statistics
- **Studies** - Medical study management interface
- **Upload Dialog** - DICOM file upload with patient selection

### Material-UI Integration
- Professional medical color scheme
- Responsive design for various screen sizes
- Accessibility features built-in
- Consistent spacing and typography

## 🔌 API Integration

### Available Services
```typescript
// Patient management
apiService.getPatients()
apiService.createPatient(data)

// Study management
apiService.getStudies()
apiService.uploadFile(file, patientId, onProgress)

// AI processing
apiService.runPrediction({study_id, model_id})

// System health
apiService.getHealth()
```

### Error Handling
- Automatic token refresh
- User-friendly error messages
- Network error recovery
- Loading states and progress indicators

## 🧪 Development Workflow

### 1. Start Backend
```bash
# From project root
python start_gui.py
```

### 2. Start Frontend
```bash
# From gui/frontend directory
npm start
```

### 3. Development Features
- **Hot Reload** - Automatic browser refresh on code changes
- **TypeScript** - Real-time type checking and IntelliSense
- **API Proxy** - Seamless backend communication
- **Error Boundaries** - Graceful error handling in UI

## 📱 Pages and Features

### Dashboard (/)
- System health monitoring
- Patient and study statistics
- Recent studies overview
- Processing queue status

### Studies (/studies)
- DICOM file upload interface
- Study listing with filtering
- AI processing status tracking
- Study details and actions

### Planned Pages
- **Patients** - Patient management interface
- **Reports** - Clinical report generation
- **Models** - AI model management
- **Settings** - System configuration

## 🎯 Next Development Steps

### Immediate Enhancements
```markdown
- [ ] Add patient management page
- [ ] Implement DICOM viewer integration
- [ ] Add report generation interface
- [ ] Create AI results visualization
- [ ] Add user authentication
```

### DICOM Viewer Integration
```bash
# Install OHIF Viewer or Cornerstone.js
npm install @ohif/viewer
# OR
npm install cornerstone-core cornerstone-tools
```

### Advanced Features
```markdown
- [ ] Real-time notifications
- [ ] Study comparison tools
- [ ] Annotation capabilities
- [ ] Export and sharing features
- [ ] Advanced filtering and search
```

## 🚀 Production Deployment

### Build for Production
```bash
npm run build
```

### Serve Static Files
The build folder can be served by the FastAPI backend or any static file server.

### Docker Integration
```dockerfile
# Frontend build stage
FROM node:16-alpine AS frontend-build
WORKDIR /app
COPY gui/frontend/package*.json ./
RUN npm ci
COPY gui/frontend/ ./
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=frontend-build /app/build /usr/share/nginx/html
```

## 🐛 Troubleshooting

### Common Issues

**"Cannot find module" errors:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**API connection issues:**
- Verify backend is running on port 8000
- Check CORS settings in backend
- Verify proxy configuration

**TypeScript errors:**
- Check tsconfig.json configuration
- Verify type definitions are installed
- Restart TypeScript language server

### Development Tips
- Use React Developer Tools browser extension
- Enable React Strict Mode for better debugging
- Use Material-UI theme inspector for styling
- Monitor network requests in browser DevTools

---

**Status**: ✅ **Frontend Foundation Complete**
**Features**: Professional medical interface with Material-UI, complete API integration, file upload, and clinical workflow support.
**Ready For**: DICOM viewer integration, advanced clinical features, and production deployment.
