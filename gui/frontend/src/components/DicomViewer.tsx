import {
    cache,
    Enums,
    getRenderingEngine,
    RenderingEngine,
    setVolumesForViewports,
    Types,
    volumeLoader,
} from '@cornerstonejs/core';
import * as cornerstoneDICOMImageLoader from '@cornerstonejs/dicom-image-loader';
import * as cornerstoneStreamingImageVolumeLoader from '@cornerstonejs/streaming-image-volume-loader';
import {
    addTool,
    AngleTool,
    ArrowAnnotateTool,
    Enums as csToolsEnums,
    EllipticalROITool,
    LengthTool,
    PanTool,
    RectangleROITool,
    StackScrollMouseWheelTool,
    ToolGroupManager,
    WindowLevelTool,
    ZoomTool,
} from '@cornerstonejs/tools';
import {
    Brightness6,
    Compare,
    CropFree,
    GetApp,
    NearMe,
    PanTool as PanIcon,
    RadioButtonUnchecked,
    Settings,
    ShowChart,
    Straighten,
    ViewInAr,
    ZoomIn
} from '@mui/icons-material';
import {
    Box,
    CircularProgress,
    Divider,
    FormControl,
    FormControlLabel,
    IconButton,
    InputLabel,
    MenuItem,
    Paper,
    Select,
    Switch,
    Toolbar,
    Tooltip,
    Typography,
} from '@mui/material';
import * as dicomParser from 'dicom-parser';
import React, { useEffect, useRef, useState } from 'react';

const { ViewportType } = Enums;
const { MouseBindings } = csToolsEnums;

interface DicomViewerProps {
  studyInstanceUID?: string;
  seriesInstanceUID?: string;
  imageIds?: string[];
  onImageLoad?: (imageData: any) => void;
  onMeasurement?: (measurement: any) => void;
  showTumorOverlay?: boolean;
  overlayAlpha?: number;
  overlayCmap?: string;
  tumorDetections?: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
    confidence: number;
    type: string;
  }>;
}

const DicomViewer: React.FC<DicomViewerProps> = ({
  studyInstanceUID,
  seriesInstanceUID,
  imageIds = [],
  onImageLoad,
  onMeasurement,
  showTumorOverlay = false,
  overlayAlpha = 0.4,
  overlayCmap = 'jet',
  tumorDetections = [],
}) => {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTools, setActiveTools] = useState<string[]>(['WindowLevel']);
  const [viewportOrientation, setViewportOrientation] = useState<string>('axial');
  const [renderingEngine, setRenderingEngine] = useState<RenderingEngine | null>(null);
  const [toolGroup, setToolGroup] = useState<any>(null);
  const [overlayUrl, setOverlayUrl] = useState<string>('');

  const renderingEngineId = 'myRenderingEngine';
  const viewportId = 'CT_AXIAL_STACK';
  const toolGroupId = 'MY_TOOLGROUP_ID';

  // Initialize Cornerstone and tools
  useEffect(() => {
    const initializeCornerstone = async () => {
      // Initialize DICOM image loader
      cornerstoneDICOMImageLoader.external.cornerstone = {
        RenderingEngine,
        Types,
        Enums,
        getRenderingEngine,
        volumeLoader,
        setVolumesForViewports,
        cache,
      };

      cornerstoneDICOMImageLoader.external.dicomParser = dicomParser;
      cornerstoneDICOMImageLoader.configure({
        useWebWorkers: true,
        decodeConfig: {
          convertFloatPixelDataToInt: false,
        },
      });

      // Initialize streaming image volume loader
      cornerstoneStreamingImageVolumeLoader.external.cornerstone = {
        RenderingEngine,
        Types,
        Enums,
        getRenderingEngine,
        volumeLoader,
        setVolumesForViewports,
        cache,
      };

      // Add tools
      addTool(WindowLevelTool);
      addTool(PanTool);
      addTool(ZoomTool);
      addTool(StackScrollMouseWheelTool);
      addTool(LengthTool);
      addTool(RectangleROITool);
      addTool(EllipticalROITool);
      addTool(AngleTool);
      addTool(ArrowAnnotateTool);

      // Create tool group
      const newToolGroup = ToolGroupManager.createToolGroup(toolGroupId);

      // Add tools to tool group
      newToolGroup?.addTool(WindowLevelTool.toolName);
      newToolGroup?.addTool(PanTool.toolName);
      newToolGroup?.addTool(ZoomTool.toolName);
      newToolGroup?.addTool(StackScrollMouseWheelTool.toolName);
      newToolGroup?.addTool(LengthTool.toolName);
      newToolGroup?.addTool(RectangleROITool.toolName);
      newToolGroup?.addTool(EllipticalROITool.toolName);
      newToolGroup?.addTool(AngleTool.toolName);
      newToolGroup?.addTool(ArrowAnnotateTool.toolName);

      // Set tool modes
      newToolGroup?.setToolActive(WindowLevelTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Primary }],
      });
      newToolGroup?.setToolActive(PanTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Auxiliary }],
      });
      newToolGroup?.setToolActive(ZoomTool.toolName, {
        bindings: [{ mouseButton: MouseBindings.Secondary }],
      });
      newToolGroup?.setToolActive(StackScrollMouseWheelTool.toolName);

      setToolGroup(newToolGroup);
    };

    initializeCornerstone();
  }, []);

  // Initialize rendering engine and viewport
  useEffect(() => {
    if (!viewportRef.current || !toolGroup) return;

    const newRenderingEngine = new RenderingEngine(renderingEngineId);
    setRenderingEngine(newRenderingEngine);

    // Create viewport
    const viewportInput = {
      viewportId,
      type: ViewportType.STACK,
      element: viewportRef.current,
    };

    newRenderingEngine.enableElement(viewportInput);

    // Add viewport to tool group
    toolGroup.addViewport(viewportId, renderingEngineId);

    return () => {
      newRenderingEngine.destroy();
      ToolGroupManager.destroyToolGroup(toolGroupId);
    };
  }, [toolGroup]);

  // Load images
  useEffect(() => {
    if (!renderingEngine || !imageIds.length) return;

    const loadImages = async () => {
      setIsLoading(true);
      try {
        const viewport = renderingEngine.getViewport(viewportId);
        await viewport.setStack(imageIds);
        viewport.render();

        if (onImageLoad) {
          onImageLoad({ imageIds, viewport });
        }
      } catch (error) {
        console.error('Failed to load images:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadImages();
  }, [renderingEngine, imageIds, onImageLoad]);

  // Compute overlay URL when controls change
  useEffect(() => {
    if (!studyInstanceUID || !showTumorOverlay) {
      setOverlayUrl('');
      return;
    }
    const ts = Date.now(); // cache buster
    const url = `/api/studies/${encodeURIComponent(
      studyInstanceUID
    )}/overlay?alpha=${encodeURIComponent(overlayAlpha)}&cmap=${encodeURIComponent(
      overlayCmap
    )}&_=${ts}`;
    setOverlayUrl(url);
  }, [studyInstanceUID, overlayAlpha, overlayCmap, showTumorOverlay]);

  // Handle tool activation
  const handleToolActivation = (toolName: string) => {
    if (!toolGroup) return;

    // Deactivate all tools first
    toolGroup.setToolPassive(WindowLevelTool.toolName);
    toolGroup.setToolPassive(PanTool.toolName);
    toolGroup.setToolPassive(ZoomTool.toolName);
    toolGroup.setToolPassive(LengthTool.toolName);
    toolGroup.setToolPassive(RectangleROITool.toolName);
    toolGroup.setToolPassive(EllipticalROITool.toolName);
    toolGroup.setToolPassive(AngleTool.toolName);
    toolGroup.setToolPassive(ArrowAnnotateTool.toolName);

    // Activate selected tool
    toolGroup.setToolActive(toolName, {
      bindings: [{ mouseButton: MouseBindings.Primary }],
    });

    // Always keep these active with different bindings
    toolGroup.setToolActive(PanTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Auxiliary }],
    });
    toolGroup.setToolActive(ZoomTool.toolName, {
      bindings: [{ mouseButton: MouseBindings.Secondary }],
    });
    toolGroup.setToolActive(StackScrollMouseWheelTool.toolName);

    setActiveTools([toolName]);
  };

  // Tool definitions for the toolbar
  const tools = [
    { name: WindowLevelTool.toolName, icon: <Brightness6 />, tooltip: 'Window/Level' },
    { name: PanTool.toolName, icon: <PanIcon />, tooltip: 'Pan' },
    { name: ZoomTool.toolName, icon: <ZoomIn />, tooltip: 'Zoom' },
    { name: LengthTool.toolName, icon: <Straighten />, tooltip: 'Measure Length' },
    { name: RectangleROITool.toolName, icon: <CropFree />, tooltip: 'Rectangle ROI' },
    { name: EllipticalROITool.toolName, icon: <RadioButtonUnchecked />, tooltip: 'Elliptical ROI' },
    { name: AngleTool.toolName, icon: <ShowChart />, tooltip: 'Angle Measurement' },
    { name: ArrowAnnotateTool.toolName, icon: <NearMe />, tooltip: 'Arrow Annotation' },
  ];

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <Toolbar variant="dense" sx={{ borderBottom: 1, borderColor: 'divider' }}>
        {/* Tool buttons */}
        {tools.map((tool) => (
          <Tooltip key={tool.name} title={tool.tooltip}>
            <IconButton
              size="small"
              color={activeTools.includes(tool.name) ? 'primary' : 'default'}
              onClick={() => handleToolActivation(tool.name)}
            >
              {tool.icon}
            </IconButton>
          </Tooltip>
        ))}

        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

        {/* Viewport controls */}
        <FormControl size="small" sx={{ minWidth: 120, mx: 1 }}>
          <InputLabel>Orientation</InputLabel>
          <Select
            value={viewportOrientation}
            label="Orientation"
            onChange={(e) => setViewportOrientation(e.target.value)}
          >
            <MenuItem value="axial">Axial</MenuItem>
            <MenuItem value="sagittal">Sagittal</MenuItem>
            <MenuItem value="coronal">Coronal</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={showTumorOverlay}
              size="small"
            />
          }
          label="Tumor Overlay"
          sx={{ mx: 1 }}
        />

        <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

        {/* Additional tools */}
        <Tooltip title="3D Rendering">
          <IconButton size="small">
            <ViewInAr />
          </IconButton>
        </Tooltip>

        <Tooltip title="Compare Studies">
          <IconButton size="small">
            <Compare />
          </IconButton>
        </Tooltip>

        <Tooltip title="Export">
          <IconButton size="small">
            <GetApp />
          </IconButton>
        </Tooltip>

        <Tooltip title="Settings">
          <IconButton size="small">
            <Settings />
          </IconButton>
        </Tooltip>
      </Toolbar>

      {/* Viewer content */}
      <Box sx={{ flex: 1, position: 'relative', bgcolor: 'black' }}>
        {isLoading && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 2,
            }}
          >
            <CircularProgress />
            <Typography variant="body2" color="white">
              Loading DICOM images...
            </Typography>
          </Box>
        )}

        <div
          ref={viewportRef}
          style={{
            width: '100%',
            height: '100%',
            cursor: 'crosshair',
          }}
        />

        {/* Simple detection boxes overlay */}
        {showTumorOverlay && tumorDetections.length > 0 && (
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 100,
            }}
          >
            {tumorDetections.map((detection, index) => (
              <Box
                key={index}
                sx={{
                  position: 'absolute',
                  left: `${detection.x}%`,
                  top: `${detection.y}%`,
                  width: `${detection.width}%`,
                  height: `${detection.height}%`,
                  border: '2px solid red',
                  borderRadius: 1,
                  bgcolor: 'rgba(255, 0, 0, 0.1)',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    position: 'absolute',
                    top: -20,
                    left: 0,
                    color: 'red',
                    fontWeight: 'bold',
                    textShadow: '1px 1px 2px black',
                  }}
                >
                  {detection.type} ({Math.round(detection.confidence * 100)}%)
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {/* Picture-in-picture overlay preview from backend PNG */}
        {showTumorOverlay && overlayUrl && (
          <Box
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              width: 256,
              height: 256,
              border: '1px solid rgba(255,255,255,0.3)',
              borderRadius: 1,
              overflow: 'hidden',
              zIndex: 120,
              bgcolor: 'rgba(0,0,0,0.5)'
            }}
          >
            {/* eslint-disable-next-line jsx-a11y/alt-text */}
            <img
              src={overlayUrl}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default DicomViewer;
