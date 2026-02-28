'use client';

import React from 'react';
import { CheckCircle, ExternalLink, AlertCircle } from 'lucide-react';

export type MedicineSource = 'internal' | 'external' | 'unknown';

interface MedicineAvailabilityBadgeProps {
  source: MedicineSource;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function MedicineAvailabilityBadge({ 
  source, 
  showLabel = true,
  size = 'md' 
}: MedicineAvailabilityBadgeProps) {
  const config = {
    internal: {
      color: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800',
      icon: CheckCircle,
      label: 'Available in Pharmacy',
      iconColor: 'text-green-500'
    },
    external: {
      color: 'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
      icon: ExternalLink,
      label: 'External Procurement',
      iconColor: 'text-amber-500'
    },
    unknown: {
      color: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-900/30 dark:text-gray-400 dark:border-gray-800',
      icon: AlertCircle,
      label: 'Availability Unknown',
      iconColor: 'text-gray-500'
    }
  };

  const { color, icon: Icon, label, iconColor } = config[source];

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-2.5 py-1 gap-1.5',
    lg: 'text-base px-3 py-1.5 gap-2'
  };

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 16
  };

  return (
    <span className={`inline-flex items-center ${sizeClasses[size]} ${color} rounded-full border font-medium`}>
      <Icon size={iconSizes[size]} className={iconColor} />
      {showLabel && <span>{label}</span>}
    </span>
  );
}

// Compact version for lists
export function MedicineSourceIndicator({ source }: { source: MedicineSource }) {
  const config = {
    internal: {
      color: 'bg-green-500',
      tooltip: 'Available in Pharmacy'
    },
    external: {
      color: 'bg-amber-500', 
      tooltip: 'External Procurement'
    },
    unknown: {
      color: 'bg-gray-400',
      tooltip: 'Availability Unknown'
    }
  };

  const { color, tooltip } = config[source];

  return (
    <div 
      className={`w-2 h-2 rounded-full ${color}`}
      title={tooltip}
    />
  );
}

export default MedicineAvailabilityBadge;
