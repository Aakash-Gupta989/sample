import { 
  Rect,
  Group,
  Text,
  FabricImage
} from 'fabric';

export const createWidget = (widget, canvas, position = { x: 100, y: 100 }) => {
  console.log('🎯 Creating widget:', widget.name, 'at position:', position);
  
  if (!canvas) {
    console.error('❌ Canvas is null or undefined');
    return null;
  }

  const { x, y } = position;
  
  try {
    // Create simple colored icon immediately (no async)
    const iconShape = createSimpleIcon(widget.id);
    
    // Create text label below the icon
    const text = new Text(widget.name, {
      left: 0,
      top: 60, // Position text below icon
      fontSize: 12,
      fontFamily: 'Inter, sans-serif',
      fontWeight: 600,
      fill: '#374151',
      textAlign: 'center',
      originX: 'center',
      originY: 'top'
    });

    // Create group with icon and text
    const widgetGroup = new Group([iconShape, text], {
      left: x,
      top: y,
      selectable: true,
      hasControls: true,
      hasBorders: true,
      cornerStyle: 'circle',
      cornerSize: 6,
      cornerColor: '#6366f1',
      borderColor: '#6366f1',
      transparentCorners: false,
      padding: 10
    });

    // Add to canvas immediately
    console.log('✅ Adding widget to canvas');
    canvas.add(widgetGroup);
    canvas.setActiveObject(widgetGroup);
    canvas.renderAll();
    console.log('✅ Widget added successfully');

    return widgetGroup;
  } catch (error) {
    console.error('❌ Error creating widget:', error);
    return null;
  }
};

// Create simple, immediate icons for widgets
const createSimpleIcon = (widgetId) => {
  const size = 50;
  const color = getWidgetColor(widgetId);
  
  // Create different shapes for different widget types
  switch (widgetId) {
    case 'database':
    case 'sql':
    case 'nosql':
      // Database cylinder shape
      return new Group([
        new Rect({ width: size, height: size * 0.6, fill: color, rx: size * 0.1, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 3, top: -size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 3, top: 0, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 3, top: size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'server':
      // Server rack
      return new Group([
        new Rect({ width: size, height: size, fill: color, rx: 4, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 4, top: -size * 0.25, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 4, top: -size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 4, top: size * 0.05, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 4, top: size * 0.2, fill: '#ffffff', originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'user':
    case 'client':
      // Person icon
      return new Group([
        new Rect({ width: size * 0.4, height: size * 0.4, top: -size * 0.2, fill: color, rx: size * 0.2, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.6, height: size * 0.4, top: size * 0.1, fill: color, rx: size * 0.1, originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'load-balancer':
      // Distribution diagram
      return new Group([
        new Rect({ width: size * 0.6, height: size * 0.2, fill: color, rx: 4, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.3, height: size * 0.15, left: -size * 0.25, top: size * 0.25, fill: color, rx: 2, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.3, height: size * 0.15, left: size * 0.25, top: size * 0.25, fill: color, rx: 2, originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'cache':
    case 'redis':
      // Cache with lightning
      return new Group([
        new Rect({ width: size, height: size * 0.6, fill: color, rx: 6, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: 2, top: -size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.6, height: 2, top: 0, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.7, height: 2, top: size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'cloud':
    case 'cdn':
      // Cloud shape
      return new Group([
        new Rect({ width: size * 0.3, height: size * 0.3, left: -size * 0.15, fill: color, rx: size * 0.15, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.4, height: size * 0.4, fill: color, rx: size * 0.2, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.25, height: size * 0.25, left: size * 0.15, fill: color, rx: size * 0.125, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.8, height: size * 0.2, top: size * 0.1, fill: color, originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'firewall':
      // Shield
      return new Group([
        new Rect({ width: size * 0.8, height: size * 0.9, fill: color, rx: size * 0.1, originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.4, height: 3, top: -size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.3, height: 3, top: 0, fill: '#ffffff', originX: 'center', originY: 'center' }),
        new Rect({ width: size * 0.35, height: 3, top: size * 0.1, fill: '#ffffff', originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    case 'monitoring':
      // Chart
      return new Group([
        new Rect({ width: size, height: size * 0.8, fill: 'transparent', stroke: color, strokeWidth: 2, rx: 4, originX: 'center', originY: 'center' }),
        new Rect({ width: 4, height: size * 0.3, left: -size * 0.25, top: size * 0.1, fill: color, originX: 'center', originY: 'center' }),
        new Rect({ width: 4, height: size * 0.4, left: -size * 0.1, top: 0, fill: color, originX: 'center', originY: 'center' }),
        new Rect({ width: 4, height: size * 0.5, left: size * 0.05, top: -size * 0.05, fill: color, originX: 'center', originY: 'center' }),
        new Rect({ width: 4, height: size * 0.6, left: size * 0.2, top: -size * 0.1, fill: color, originX: 'center', originY: 'center' })
      ], { originX: 'center', originY: 'center' });
      
    default:
      // Default rectangle
      return new Rect({
        width: size * 0.8,
        height: size * 0.8,
        fill: color,
        rx: 8,
        ry: 8,
        originX: 'center',
        originY: 'center'
      });
  }
};

// Create custom high-definition illustrations for each widget (UNUSED - keeping for future)
const createCustomIllustration = async (widgetId) => {
  const size = 50;
  
  // Custom SVG illustrations with detailed, colorful designs
  const illustrations = {
    'database': `<svg width="${size}" height="${size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="dbGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#4F46E5;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#3B82F6;stop-opacity:1" />
        </linearGradient>
      </defs>
      <ellipse cx="32" cy="16" rx="24" ry="8" fill="url(#dbGrad)" stroke="#1E40AF" stroke-width="2"/>
      <rect x="8" y="16" width="48" height="32" fill="url(#dbGrad)" stroke="#1E40AF" stroke-width="2"/>
      <ellipse cx="32" cy="48" rx="24" ry="8" fill="url(#dbGrad)" stroke="#1E40AF" stroke-width="2"/>
      <rect x="12" y="22" width="40" height="2" fill="#60A5FA"/>
      <rect x="12" y="28" width="40" height="2" fill="#60A5FA"/>
      <rect x="12" y="34" width="40" height="2" fill="#60A5FA"/>
      <rect x="12" y="40" width="40" height="2" fill="#60A5FA"/>
    </svg>`,
    
    'server': `<svg width="${size}" height="${size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="serverGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#1E40AF;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1E3A8A;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect x="8" y="8" width="48" height="48" rx="4" fill="url(#serverGrad)" stroke="#0F172A" stroke-width="2"/>
      <rect x="12" y="14" width="40" height="6" rx="2" fill="#3B82F6"/>
      <rect x="12" y="24" width="40" height="6" rx="2" fill="#3B82F6"/>
      <rect x="12" y="34" width="40" height="6" rx="2" fill="#3B82F6"/>
      <rect x="12" y="44" width="40" height="6" rx="2" fill="#3B82F6"/>
      <circle cx="46" cy="17" r="2" fill="#10B981"/>
      <circle cx="46" cy="27" r="2" fill="#10B981"/>
      <circle cx="46" cy="37" r="2" fill="#EF4444"/>
      <circle cx="46" cy="47" r="2" fill="#10B981"/>
    </svg>`,
    
    'user': `<svg width="${size}" height="${size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="userGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#059669;stop-opacity:1" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="20" r="12" fill="url(#userGrad)" stroke="#047857" stroke-width="2"/>
      <path d="M12 52 Q12 36 32 36 Q52 36 52 52 L52 56 L12 56 Z" fill="url(#userGrad)" stroke="#047857" stroke-width="2"/>
    </svg>`,
    
    'client': `<svg width="${size}" height="${size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="clientGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#8B5CF6;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#7C3AED;stop-opacity:1" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="20" r="12" fill="url(#clientGrad)" stroke="#6D28D9" stroke-width="2"/>
      <path d="M12 52 Q12 36 32 36 Q52 36 52 52 L52 56 L12 56 Z" fill="url(#clientGrad)" stroke="#6D28D9" stroke-width="2"/>
      <circle cx="32" cy="32" r="20" fill="none" stroke="#A855F7" stroke-width="2" stroke-dasharray="4,4"/>
    </svg>`,
    
    'cache': `<svg width="${size}" height="${size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="cacheGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#F59E0B;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#D97706;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect x="8" y="16" width="48" height="32" rx="6" fill="url(#cacheGrad)" stroke="#B45309" stroke-width="2"/>
      <rect x="12" y="22" width="40" height="3" fill="#FCD34D"/>
      <rect x="12" y="28" width="32" height="3" fill="#FCD34D"/>
      <rect x="12" y="34" width="36" height="3" fill="#FCD34D"/>
      <rect x="12" y="40" width="28" height="3" fill="#FCD34D"/>
      <path d="M48 8 L44 16 L48 16 L42 24 L48 16 L44 16 Z" fill="#FBBF24" stroke="#D97706" stroke-width="1"/>
    </svg>`,
    
    'load-balancer': `<svg width="${size}" height="${size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="lbGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#06B6D4;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#0891B2;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect x="20" y="8" width="24" height="12" rx="4" fill="url(#lbGrad)" stroke="#0E7490" stroke-width="2"/>
      <rect x="8" y="32" width="16" height="10" rx="3" fill="#67E8F9" stroke="#0891B2" stroke-width="1"/>
      <rect x="40" y="32" width="16" height="10" rx="3" fill="#67E8F9" stroke="#0891B2" stroke-width="1"/>
      <rect x="24" y="48" width="16" height="10" rx="3" fill="#67E8F9" stroke="#0891B2" stroke-width="1"/>
      <line x1="32" y1="20" x2="16" y2="32" stroke="#0891B2" stroke-width="2"/>
      <line x1="32" y1="20" x2="48" y2="32" stroke="#0891B2" stroke-width="2"/>
      <line x1="32" y1="20" x2="32" y2="48" stroke="#0891B2" stroke-width="2"/>
    </svg>`
  };

  // Get the custom illustration or use default
  const svgString = illustrations[widgetId] || illustrations['database'];
  
  return new Promise((resolve, reject) => {
    try {
      // Convert SVG to data URL
      const svgDataUrl = `data:image/svg+xml;base64,${btoa(svgString)}`;
      
      // Create Fabric.js Image
      FabricImage.fromURL(svgDataUrl, (img) => {
        if (img) {
          img.set({
            left: 0,
            top: 0,
            scaleX: 1,
            scaleY: 1,
            originX: 'center',
            originY: 'center'
          });
          resolve(img);
        } else {
          reject(new Error('Failed to create image from SVG'));
        }
      });
    } catch (error) {
      reject(error);
    }
  });
};

// Get widget color for fallback
const getWidgetColor = (widgetId) => {
  const colors = {
    'database': '#3B82F6',
    'sql': '#F59E0B',
    'nosql': '#059669',
    'server': '#1E40AF',
    'user': '#10B981',
    'client': '#8B5CF6',
    'service': '#F59E0B',
    'firewall': '#EF4444',
    'monitoring': '#10B981',
    'load-balancer': '#06B6D4',
    'cache': '#F59E0B',
    'redis': '#DC2626',
    'cdn': '#06B6D4',
    'cloud': '#3B82F6',
    'api-gateway': '#8B5CF6',
    'rate-limiter': '#EF4444',
    'cluster-manager': '#059669',
    'auto-scale': '#7C3AED',
    'aws-elastic-search': '#F59E0B',
    'ml-ai-engine': '#EC4899',
    'data-structure': '#0EA5E9',
    'worker': '#059669',
    'batch-process': '#7C2D12',
    'shared-counters': '#0891B2',
    'transformer': '#7C3AED',
    'binary-data': '#374151',
    'blob-storage': '#0EA5E9',
    'dns': '#7C3AED',
    'shard-manager': '#DC2626'
  };
  return colors[widgetId] || '#6366f1';
};
