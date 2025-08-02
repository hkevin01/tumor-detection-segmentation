import React, { useEffect, useRef, useState } from 'react';
import * as cornerstone from '@cornerstonejs/core';
import * as cornerstoneTools from '@cornerstonejs/tools';
import { ViewportType } from '@cornerstonejs/core/dist/esm/enums';
import {
  PanTool,
  ZoomTool,
  WindowLevelTool,
  StackScrollTool,
  LengthTool,
  SegmentationDisplayTool,
} from '@cornerstonejs/tools';

interface Props {
  imageId?: string;
  segmentationData?: number[][][];
  onMeasurementComplete?: (measurements: any) => void;
}

const MedicalImageViewer: React.FC<Props> = ({
  imageId,
  segmentationData,
  onMeasurementComplete,
}) => {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [viewportId, setViewportId] = useState<string>('');
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initializeViewer = async () => {
      // Initialize Cornerstone if not already done
      if (!isInitialized) {
        await cornerstone.init();
        
        // Register tools
        cornerstoneTools.addTool(PanTool);
        cornerstoneTools.addTool(ZoomTool);
        cornerstoneTools.addTool(WindowLevelTool);
        cornerstoneTools.addTool(StackScrollTool);
        cornerstoneTools.addTool(LengthTool);
        cornerstoneTools.addTool(SegmentationDisplayTool);

        setIsInitialized(true);
      }

      if (viewportRef.current) {
        // Create the viewport
        const viewport = await cornerstone.enableElement({
          element: viewportRef.current,
          type: ViewportType.STACK,
        });

        setViewportId(viewport.id);

        // Set up default tools
        cornerstoneTools.setToolActive('Pan', { bindings: [{ mouseButton: 2 }] });
        cornerstoneTools.setToolActive('Zoom', { bindings: [{ mouseButton: 3 }] });
        cornerstoneTools.setToolActive('WindowLevel', { bindings: [{ mouseButton: 1 }] });
        cornerstoneTools.setToolActive('StackScroll', { bindings: [{ mouseButton: 2 }] });
      }
    };

    initializeViewer();

    return () => {
      // Cleanup
      if (viewportRef.current) {
        cornerstone.disableElement(viewportRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const loadImage = async () => {
      if (imageId && viewportId && viewportRef.current) {
        try {
          // Load and display the image
          const image = await cornerstone.loadImage(imageId);
          await cornerstone.setVolume(viewportId, image);
          
          // Reset view
          cornerstone.resetCamera(viewportId);
        } catch (error) {
          console.error('Error loading image:', error);
        }
      }
    };

    loadImage();
  }, [imageId, viewportId]);

  useEffect(() => {
    const displaySegmentation = async () => {
      if (segmentationData && viewportId) {
        try {
          // Convert segmentation data to the format expected by Cornerstone
          const segmentation = {
            dimensions: [
              segmentationData.length,
              segmentationData[0].length,
              segmentationData[0][0].length,
            ],
            data: new Float32Array(segmentationData.flat(2)),
          };

          // Add segmentation to viewport
          await cornerstone.addSegmentation(viewportId, segmentation);
        } catch (error) {
          console.error('Error displaying segmentation:', error);
        }
      }
    };

    displaySegmentation();
  }, [segmentationData, viewportId]);

  return (
    <div className="medical-image-viewer">
      <div 
        ref={viewportRef}
        style={{ width: '100%', height: '600px', backgroundColor: '#000' }}
      />
      <div className="toolbar">
        <button onClick={() => cornerstoneTools.setToolActive('Length')}>
          Measure
        </button>
        <button onClick={() => cornerstoneTools.setToolActive('WindowLevel')}>
          Window/Level
        </button>
        <button onClick={() => cornerstoneTools.setToolActive('Pan')}>
          Pan
        </button>
        <button onClick={() => cornerstoneTools.setToolActive('Zoom')}>
          Zoom
        </button>
        <button onClick={() => cornerstone.resetCamera(viewportId)}>
          Reset View
        </button>
      </div>
    </div>
  );
};

export default MedicalImageViewer;
