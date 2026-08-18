import React from 'react';
import {
  Scale,
  Footprints,
  Camera,
  HeartPulse,
  Flame,
  Droplets,
  Activity,
  Award,
  Layers,
  Sparkles,
  Zap,
  Target
} from 'lucide-react';

const ICON_MAP = {
  Scale,
  Footprints,
  Camera,
  HeartPulse,
  Flame,
  Droplets,
  Activity,
  Award,
  Layers,
  Sparkles,
  Zap,
  Target
};

/**
 * Returns the matching Lucide React Icon element for a manifest icon string.
 */
export function getPluginIcon(iconName, props = {}) {
  const IconComponent = ICON_MAP[iconName] || Activity;
  return React.createElement(IconComponent, props);
}

/**
 * Default fallback colors for categories
 */
export function getCategoryBadgeColor(category) {
  switch (category) {
    case 'body_composition':
      return { bg: 'rgba(5, 150, 105, 0.15)', text: '#059669', border: 'rgba(5, 150, 105, 0.3)' };
    case 'activity':
      return { bg: 'rgba(37, 99, 235, 0.15)', text: '#2563eb', border: 'rgba(37, 99, 235, 0.3)' };
    case 'equipment':
      return { bg: 'rgba(79, 70, 229, 0.15)', text: '#4f46e5', border: 'rgba(79, 70, 229, 0.3)' };
    default:
      return { bg: 'rgba(100, 116, 139, 0.15)', text: '#64748b', border: 'rgba(100, 116, 139, 0.3)' };
  }
}
