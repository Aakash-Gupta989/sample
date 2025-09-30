import React from 'react';
import { 
  Database, 
  Server, 
  Users, 
  Globe, 
  Zap, 
  Shield, 
  BarChart3, 
  Cpu, 
  HardDrive, 
  Cloud, 
  Network, 
  Lock, 
  Activity, 
  Settings, 
  Search, 
  FileText, 
  Layers, 
  GitBranch, 
  Timer, 
  Gauge, 
  Workflow, 
  Binary, 
  Boxes, 
  Cog, 
  MonitorSpeaker, 
  Wifi, 
  CloudCog 
} from 'lucide-react';

const WidgetPanel = ({ isOpen, onWidgetSelect }) => {
  const widgets = [
    { id: 'database', name: 'Database', icon: Database },
    { id: 'server', name: 'Server', icon: Server },
    { id: 'user', name: 'User', icon: Users },
    { id: 'client', name: 'Client', icon: Globe },
    { id: 'service', name: 'Service', icon: Zap },
    { id: 'firewall', name: 'Firewall', icon: Shield },
    { id: 'monitoring', name: 'Monitoring', icon: BarChart3 },
    { id: 'load-balancer', name: 'Load Balancer', icon: Cpu },
    { id: 'cache', name: 'Cache', icon: HardDrive },
    { id: 'cdn', name: 'CDN', icon: Cloud },
    { id: 'api-gateway', name: 'API Gateway', icon: Network },
    { id: 'rate-limiter', name: 'Rate Limiter', icon: Lock },
    { id: 'cluster-manager', name: 'Cluster Manager', icon: Activity },
    { id: 'auto-scale', name: 'Auto Scale', icon: Settings },
    { id: 'aws-elastic-search', name: 'AWS Elastic Search', icon: Search },
    { id: 'ml-ai-engine', name: 'ML/AI Engine', icon: FileText },
    { id: 'data-structure', name: 'Data Structure', icon: Layers },
    { id: 'worker', name: 'Worker', icon: GitBranch },
    { id: 'batch-process', name: 'Batch Process', icon: Timer },
    { id: 'shared-counters', name: 'Shared Counters', icon: Gauge },
    { id: 'transformer', name: 'Transformer', icon: Workflow },
    { id: 'binary-data', name: 'Binary Data', icon: Binary },
    { id: 'blob-storage', name: 'Blob Storage', icon: Boxes },
    { id: 'redis', name: 'Redis', icon: Cog },
    { id: 'nosql', name: 'NoSQL', icon: MonitorSpeaker },
    { id: 'sql', name: 'SQL', icon: Database },
    { id: 'dns', name: 'DNS', icon: Wifi },
    { id: 'shard-manager', name: 'Shard Manager', icon: CloudCog }
  ];

  const handleWidgetClick = (widget) => {
    console.log('🎯 Widget panel - widget clicked:', widget);
    if (onWidgetSelect) {
      onWidgetSelect(widget);
    } else {
      console.error('❌ onWidgetSelect callback not provided');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="widget-panel">
      <div className="widget-panel-header">
        <span>System Design Widgets</span>
      </div>
      <div className="widget-grid">
        {widgets.map((widget) => {
          const IconComponent = widget.icon;
          return (
            <div
              key={widget.id}
              className="widget-item"
              onClick={() => handleWidgetClick(widget)}
              title={widget.name}
            >
              <IconComponent size={20} />
              <span className="widget-name">{widget.name}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default WidgetPanel;
