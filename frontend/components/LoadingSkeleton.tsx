'use client';

import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ 
  className = '', 
  variant = 'rectangular', 
  width, 
  height 
}: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-slate-200 dark:bg-slate-700';
  
  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
}

// Chat Message Skeleton
export function MessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-2`}>
        <Skeleton variant="circular" width={32} height={32} />
        <div className="space-y-2">
          <Skeleton width={200} height={60} />
          <Skeleton width={150} height={16} />
        </div>
      </div>
    </div>
  );
}

// Medicine Card Skeleton
export function MedicineCardSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-4 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton variant="rectangular" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={20} />
          <Skeleton width="40%" height={16} />
        </div>
        <Skeleton width={60} height={24} />
      </div>
      <Skeleton width="100%" height={40} />
    </div>
  );
}

// Chat Window Skeleton
export function ChatWindowSkeleton() {
  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton width={150} height={24} />
            <Skeleton width={200} height={16} />
          </div>
          <Skeleton width={100} height={32} className="rounded-full" />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        <MessageSkeleton isUser={false} />
        <MessageSkeleton isUser={true} />
        <MessageSkeleton isUser={false} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700">
        <Skeleton width="100%" height={50} />
      </div>
    </div>
  );
}

// Sidebar Skeleton
export function SidebarSkeleton() {
  return (
    <div className="w-64 h-full bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 flex flex-col p-4 space-y-4">
      <Skeleton width={150} height={30} />
      <Skeleton width="100%" height={40} />
      <div className="flex-1 space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} width="100%" height={48} />
        ))}
      </div>
      <Skeleton width="100%" height={40} />
      <Skeleton width="100%" height={40} />
    </div>
  );
}

// Typing Indicator
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-2">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}
