import { 
  Rect as FabricRect, 
  Circle as FabricCircle, 
  Line as FabricLine, 
  Polygon as FabricPolygon,
  IText as FabricText,
  Group as FabricGroup
} from 'fabric';

// High-definition shape creation utilities
export const createShape = (type, options = {}) => {
  const defaultOptions = {
    left: options.x || 100,
    top: options.y || 100,
    fill: 'transparent',
    stroke: '#000000',
    strokeWidth: 2,
    selectable: true,
    evented: true,
    hasControls: true,
    hasBorders: true,
    cornerStyle: 'circle',
    cornerSize: 8,
    transparentCorners: false,
    cornerColor: '#6366f1',
    cornerStrokeColor: '#ffffff',
    borderColor: '#6366f1',
    borderScaleFactor: 2,
    ...options
  };

  switch (type) {
    case 'rectangle':
      return new FabricRect({
        ...defaultOptions,
        width: options.width || 100,
        height: options.height || 60,
        rx: 4, // Slight border radius for modern look
        ry: 4
      });

    case 'circle':
      return new FabricCircle({
        ...defaultOptions,
        radius: options.radius || 40,
        originX: 'center',
        originY: 'center'
      });

    case 'diamond':
      const diamondPoints = [
        { x: 0, y: -40 },    // Top
        { x: 40, y: 0 },     // Right  
        { x: 0, y: 40 },     // Bottom
        { x: -40, y: 0 }     // Left
      ];
      return new FabricPolygon(diamondPoints, {
        ...defaultOptions,
        originX: 'center',
        originY: 'center'
      });

    case 'line':
      return new FabricLine([0, 0, 100, 0], {
        ...defaultOptions,
        fill: undefined, // Lines don't have fill
        strokeLineCap: 'round'
      });

    case 'arrow':
      // Create a simple arrow using polygon points
      try {
        const arrowPoints = [
          { x: 0, y: 0 },     // Start point
          { x: 60, y: 0 },    // Line to near end
          { x: 50, y: -10 },  // Arrow head top
          { x: 80, y: 0 },    // Arrow tip
          { x: 50, y: 10 },   // Arrow head bottom
          { x: 60, y: 0 },    // Back to line
          { x: 0, y: 0 }      // Close path
        ];

        return new FabricPolygon(arrowPoints, {
          ...defaultOptions,
          fill: defaultOptions.stroke || '#000000',
          stroke: defaultOptions.stroke || '#000000',
          strokeWidth: 1
        });
      } catch (error) {
        console.error('Error creating arrow:', error);
        // Fallback to simple line with arrow text
        return new FabricLine([0, 0, 80, 0], {
          ...defaultOptions,
          fill: undefined,
          strokeLineCap: 'round'
        });
      }

    case 'text':
      return new FabricText('Text', {
        ...defaultOptions,
        fontSize: 16,
        fontFamily: 'Inter, sans-serif',
        fill: '#000000',
        stroke: undefined,
        strokeWidth: 0
      });

    case 'polygon':
      // Create a hexagon
      const hexPoints = [];
      const sides = 6;
      const radius = 40;
      for (let i = 0; i < sides; i++) {
        const angle = (i * 2 * Math.PI) / sides;
        hexPoints.push({
          x: radius * Math.cos(angle),
          y: radius * Math.sin(angle)
        });
      }
      return new FabricPolygon(hexPoints, {
        ...defaultOptions,
        originX: 'center',
        originY: 'center'
      });

    default:
      return null;
  }
};

// Add shape to canvas with mouse interaction
export const addShapeToCanvas = (canvas, shapeType, startX, startY) => {
  if (!canvas) return null;

  const shape = createShape(shapeType, {
    x: startX,
    y: startY
  });

  if (shape) {
    canvas.add(shape);
    canvas.setActiveObject(shape);
    canvas.renderAll();
    return shape;
  }

  return null;
};

// Handle mouse events for shape creation
export const setupShapeCreation = (canvas, shapeType, onShapeCreated) => {
  if (!canvas) return;

  try {
    // Remove ALL existing event listeners first
    canvas.off('mouse:down');
    canvas.off('mouse:move');
    canvas.off('mouse:up');

    // For shape creation tools, add ONE-TIME event listener
    if (['rectangle', 'circle', 'diamond', 'line', 'arrow', 'polygon', 'text'].includes(shapeType)) {
      
      const createShapeOnce = (e) => {
        const pointer = canvas.getPointer(e.e);
        
        // Create the shape
        addShapeToCanvas(canvas, shapeType, pointer.x, pointer.y);
        
        // Remove this event listener immediately after use
        canvas.off('mouse:down', createShapeOnce);
        
        // Switch back to select tool
        if (onShapeCreated) {
          setTimeout(() => {
            onShapeCreated();
          }, 50);
        }
      };

      // Add the one-time event listener
      canvas.on('mouse:down', createShapeOnce);
    }
  } catch (error) {
    console.error('Error setting up shape creation:', error);
  }
};
