declare module '@cornerstonejs/core' {
  export function init(): Promise<void>;
  export function enableElement(options: { element: HTMLElement; type: string }): Promise<any>;
  export function disableElement(element: HTMLElement): void;
  export function loadImage(imageId: string): Promise<any>;
  export function setVolume(viewportId: string, image: any): Promise<void>;
  export function resetCamera(viewportId: string): void;
  export function addSegmentation(viewportId: string, segmentation: any): Promise<void>;
}

declare module '@cornerstonejs/tools' {
  export function addTool(tool: any): void;
  export function setToolActive(toolName: string, options?: any): void;
}

declare module '@cornerstonejs/core/dist/esm/enums' {
  export enum ViewportType {
    STACK = 'stack',
    ORTHOGRAPHIC = 'orthographic',
    VOLUME = 'volume'
  }
}
