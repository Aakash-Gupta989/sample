import React, { useState, useEffect, useRef } from 'react';
import { 
  Lock, 
  Hand, 
  MousePointer, 
  Square, 
  Diamond, 
  Circle, 
  ArrowRight, 
  Minus, 
  Edit3, 
  Type, 
  Image,
  Hexagon,
  Eraser,
  Trash2,
  Library
} from 'lucide-react';

const Toolbar = ({ onToolSelect, selectedTool, fabricCanvas, onLibraryToggle }) => {
  const [activeTool, setActiveTool] = useState('select');
  const [isLocked, setIsLocked] = useState(false);
  const [position, setPosition] = useState({ x: 100, y: 20 }); // Start slightly more RIGHT
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [toolbarSize, setToolbarSize] = useState({ width: 0, height: 0 });
  const animationFrameRef = useRef(null);
  const canvasBoundsRef = useRef(null);
  const lastMousePos = useRef({ x: 0, y: 0 });

  const tools = [
    { id: 'lock', icon: Lock, shortcut: '1', tooltip: 'Lock/Unlock' },
    { id: 'hand', icon: Hand, shortcut: '2', tooltip: 'Hand Tool (Pan)' },
    { id: 'select', icon: MousePointer, shortcut: '3', tooltip: 'Select Tool' },
    { id: 'rectangle', icon: Square, shortcut: '4', tooltip: 'Rectangle' },
    { id: 'diamond', icon: Diamond, shortcut: '5', tooltip: 'Diamond' },
    { id: 'circle', icon: Circle, shortcut: '6', tooltip: 'Circle' },
    { id: 'polygon', icon: Hexagon, shortcut: '7', tooltip: 'Polygon' },
    { id: 'arrow', icon: ArrowRight, shortcut: '8', tooltip: 'Arrow' },
    { id: 'line', icon: Minus, shortcut: '9', tooltip: 'Line' },
    { id: 'pen', icon: Edit3, shortcut: 'P', tooltip: 'Pen Tool' },
    { id: 'eraser', icon: Eraser, shortcut: 'E', tooltip: 'Eraser' },
    { id: 'text', icon: Type, shortcut: 'T', tooltip: 'Text' },
    { id: 'clear', icon: Trash2, shortcut: 'C', tooltip: 'Clear All' },
    { id: 'library', icon: Library, shortcut: 'L', tooltip: 'Library' }
  ];

  // Handle tool selection
  const handleToolClick = (toolId) => {
    // Handle special actions
    if (toolId === 'clear') {
      clearCanvas();
      return;
    }
    
    if (toolId === 'lock') {
      setIsLocked(!isLocked);
      return;
    }

    if (toolId === 'library') {
      if (onLibraryToggle) {
        onLibraryToggle();
      }
      return;
    }

    setActiveTool(toolId);
    if (onToolSelect) {
      onToolSelect(toolId);
    }
    
    // Apply tool functionality to canvas
    if (fabricCanvas) {
      applyToolToCanvas(toolId);
    }
  };

  // Clear canvas function
  const clearCanvas = () => {
    if (fabricCanvas) {
      fabricCanvas.clear();
      fabricCanvas.renderAll();
    }
  };

  // Auto-switch back to select after creating a shape
  const switchToSelect = () => {
    console.log('🔄 Switching back to select tool');
    setActiveTool('select');
    if (onToolSelect) {
      onToolSelect('select');
    }
    if (fabricCanvas) {
      applyToolToCanvas('select');
      // Clear any remaining event listeners
      fabricCanvas.off('mouse:down');
      fabricCanvas.off('mouse:move');
      fabricCanvas.off('mouse:up');
    }
  };

  // Cache canvas bounds for performance
  const updateCanvasBounds = () => {
    const canvasArea = document.querySelector('.canvas-area');
    if (canvasArea) {
      const rect = canvasArea.getBoundingClientRect();
      canvasBoundsRef.current = {
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height
      };
    }
  };

  // Constrain position within canvas bounds (optimized)
  const constrainPosition = (newX, newY) => {
    if (!canvasBoundsRef.current) return { x: newX, y: newY };
    
    const margin = 10;
    const bounds = canvasBoundsRef.current;
    
    // Constrain within canvas area bounds
    const constrainedX = Math.max(
      margin,
      Math.min(newX, bounds.width - toolbarSize.width - margin)
    );
    
    const constrainedY = Math.max(
      margin,
      Math.min(newY, bounds.height - toolbarSize.height - margin)
    );
    
    return { x: constrainedX, y: constrainedY };
  };

  // Drag functionality with performance optimization
  const handleMouseDown = (e) => {
    if (isLocked) return;
    
    setIsDragging(true);
    updateCanvasBounds(); // Cache bounds at start of drag
    
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
    
    // Update toolbar size for boundary calculations
    setToolbarSize({
      width: rect.width,
      height: rect.height
    });
  };

  const handleMouseMove = (e) => {
    if (!isDragging || isLocked || !canvasBoundsRef.current) return;
    
    // Store current mouse position
    lastMousePos.current = { x: e.clientX, y: e.clientY };
    
    // Cancel previous animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    // Use requestAnimationFrame for smooth updates
    animationFrameRef.current = requestAnimationFrame(() => {
      const bounds = canvasBoundsRef.current;
      const mousePos = lastMousePos.current;
      
      // Calculate position relative to canvas area
      const newX = mousePos.x - bounds.left - dragOffset.x;
      const newY = mousePos.y - bounds.top - dragOffset.y;
      
      const constrainedPos = constrainPosition(newX, newY);
      setPosition(constrainedPos);
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  };

  // Add global mouse event listeners for dragging
  useEffect(() => {
    if (isDragging) {
      // Use passive listeners for better performance
      document.addEventListener('mousemove', handleMouseMove, { passive: true });
      document.addEventListener('mouseup', handleMouseUp, { passive: true });
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        // Clean up animation frame on unmount
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }
      };
    }
  }, [isDragging, dragOffset, isLocked]);

  // Cleanup animation frame on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Apply tool functionality to Fabric.js canvas
  const applyToolToCanvas = (toolId) => {
    if (!fabricCanvas) return;

    try {
      // Reset canvas interaction mode
      fabricCanvas.isDrawingMode = false;
      fabricCanvas.selection = true;
      
      // Safely set cursor properties
      if (fabricCanvas.defaultCursor !== undefined) {
        fabricCanvas.defaultCursor = 'default';
      }
      if (fabricCanvas.hoverCursor !== undefined) {
        fabricCanvas.hoverCursor = 'move';
      }
      if (fabricCanvas.moveCursor !== undefined) {
        fabricCanvas.moveCursor = 'move';
      }

      switch (toolId) {
        case 'lock':
          // Toggle selection for all objects
          fabricCanvas.forEachObject((obj) => {
            obj.selectable = !obj.selectable;
            obj.evented = !obj.evented;
          });
          break;
        
        case 'hand':
          if (fabricCanvas.defaultCursor !== undefined) {
            fabricCanvas.defaultCursor = 'grab';
          }
          if (fabricCanvas.hoverCursor !== undefined) {
            fabricCanvas.hoverCursor = 'grab';
          }
          if (fabricCanvas.moveCursor !== undefined) {
            fabricCanvas.moveCursor = 'grabbing';
          }
          fabricCanvas.selection = false;
          break;
        
        case 'select':
          if (fabricCanvas.defaultCursor !== undefined) {
            fabricCanvas.defaultCursor = 'default';
          }
          fabricCanvas.selection = true;
          break;
        
        case 'pen':
          fabricCanvas.isDrawingMode = true;
          fabricCanvas.selection = false;
          // Ensure brush exists and configure it
          if (!fabricCanvas.freeDrawingBrush) {
            // Import PencilBrush and create new instance
            import('fabric').then(({ PencilBrush }) => {
              fabricCanvas.freeDrawingBrush = new PencilBrush(fabricCanvas);
              fabricCanvas.freeDrawingBrush.width = 2;
              fabricCanvas.freeDrawingBrush.color = '#000000';
            });
          } else {
            fabricCanvas.freeDrawingBrush.width = 2;
            fabricCanvas.freeDrawingBrush.color = '#000000';
          }
          if (fabricCanvas.defaultCursor !== undefined) {
            fabricCanvas.defaultCursor = 'crosshair';
          }
          break;
        
        case 'eraser':
          fabricCanvas.isDrawingMode = true;
          fabricCanvas.selection = false;
          // Set eraser properties - use larger brush and white color
          if (fabricCanvas.freeDrawingBrush) {
            fabricCanvas.freeDrawingBrush.width = 20;
            fabricCanvas.freeDrawingBrush.color = '#ffffff';
          }
          break;
        
        case 'rectangle':
        case 'circle':
        case 'diamond':
        case 'line':
        case 'arrow':
        case 'polygon':
          if (fabricCanvas.defaultCursor !== undefined) {
            fabricCanvas.defaultCursor = 'crosshair';
          }
          fabricCanvas.selection = false;
          break;
        
        case 'text':
          if (fabricCanvas.defaultCursor !== undefined) {
            fabricCanvas.defaultCursor = 'text';
          }
          fabricCanvas.selection = false;
          break;
        
        default:
          break;
      }
      
      fabricCanvas.renderAll();
    } catch (error) {
      console.error('Error applying tool to canvas:', error);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Only handle shortcuts if not typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      const shortcutMap = {
        '1': 'lock',
        '2': 'hand', 
        '3': 'select',
        '4': 'rectangle',
        '5': 'diamond',
        '6': 'circle',
        '7': 'polygon',
        '8': 'arrow',
        '9': 'line',
        'p': 'pen',
        'P': 'pen',
        'e': 'eraser',
        'E': 'eraser',
        't': 'text',
        'T': 'text',
        'c': 'clear',
        'C': 'clear',
        'l': 'library',
        'L': 'library'
      };

      if (shortcutMap[e.key]) {
        e.preventDefault();
        handleToolClick(shortcutMap[e.key]);
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  // Initialize toolbar position on first load - left side, middle vertically
  useEffect(() => {
    const initializePosition = () => {
      const canvasArea = document.querySelector('.canvas-area');
      if (canvasArea) {
        const rect = canvasArea.getBoundingClientRect();
        updateCanvasBounds(); // Initialize bounds cache
        
        // Position toolbar centered by moving LEFT
        const canvasWidth = rect.width;
        const toolbarWidth = 500; // Accurate toolbar width with LIBRARY text
        const centerX = (canvasWidth - toolbarWidth) / 2;
        
        setPosition({
          x: Math.max(10, centerX - 60), // Move slightly RIGHT (less LEFT offset)
          y: 20  // Keep the height position
        });
        
        // Set initial toolbar size estimate
        setToolbarSize({
          width: 400, // Approximate toolbar width
          height: 100  // Approximate toolbar height
        });
      }
    };

    // Wait a bit for DOM to be ready
    const timer = setTimeout(initializePosition, 100);
    return () => clearTimeout(timer);
  }, []);

  // Sync with external selectedTool prop
  useEffect(() => {
    if (selectedTool && selectedTool !== activeTool) {
      setActiveTool(selectedTool);
    }
  }, [selectedTool]);

  return (
    <div 
      className={`toolbar ${isLocked ? 'locked' : 'floating'} ${isDragging ? 'dragging' : ''}`}
      style={{
        left: position.x,
        top: position.y,
        cursor: isLocked ? 'default' : (isDragging ? 'grabbing' : 'grab')
      }}
      onMouseDown={handleMouseDown}
    >
      <div className="toolbar-container">
        {tools.map((tool) => {
          const IconComponent = tool.icon;
          const isActive = tool.id === 'lock' ? isLocked : (activeTool === tool.id);
          
          return (
            <button
              key={tool.id}
              className={`toolbar-tool ${isActive ? 'active' : ''} ${tool.id === 'library' ? 'library-button' : ''}`}
              onClick={() => handleToolClick(tool.id)}
              title={`${tool.tooltip} (${tool.shortcut})`}
              data-shortcut={tool.shortcut}
              onMouseDown={(e) => e.stopPropagation()}
            >
              {tool.id === 'library' ? (
                <span className="library-text">LIBRARY</span>
              ) : (
                <>
                  <IconComponent size={18} strokeWidth={1.5} />
                  <span className="tool-shortcut">{tool.shortcut}</span>
                </>
              )}
            </button>
          );
        })}
      </div>
      
    </div>
  );
};

export default Toolbar;
