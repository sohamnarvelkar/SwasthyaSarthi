'use client';

import React, { useState, useEffect } from 'react';
import { CheckCircle, Package, Truck, Mail, Clock, MapPin, Phone, X } from 'lucide-react';

export interface OrderDetails {
  order_id: string;
  medicine_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  delivery_address?: string;
  status: 'confirmed' | 'processing' | 'shipped' | 'delivered';
  estimated_delivery?: string;
  customer_email?: string;
}

interface OrderConfirmationProps {
  order: OrderDetails;
  onClose?: () => void;
  compact?: boolean;
}

export function OrderConfirmation({ order, onClose, compact = false }: OrderConfirmationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [animateStep, setAnimateStep] = useState(0);

  useEffect(() => {
    // Trigger animations sequentially
    const timers = [
      setTimeout(() => setIsVisible(true), 100),
      setTimeout(() => setAnimateStep(1), 600),
      setTimeout(() => setAnimateStep(2), 1200),
      setTimeout(() => setAnimateStep(3), 1800),
    ];

    return () => timers.forEach(clearTimeout);
  }, []);

  const getStatusIcon = () => {
    switch (order.status) {
      case 'confirmed':
        return <CheckCircle className="text-green-500" size={24} />;
      case 'processing':
        return <Package className="text-blue-500" size={24} />;
      case 'shipped':
        return <Truck className="text-purple-500" size={24} />;
      case 'delivered':
        return <CheckCircle className="text-teal-500" size={24} />;
    }
  };

  const getStatusText = () => {
    switch (order.status) {
      case 'confirmed':
        return 'Order Confirmed';
      case 'processing':
        return 'Being Prepared';
      case 'shipped':
        return 'On the Way';
      case 'delivered':
        return 'Delivered';
    }
  };

  if (compact) {
    return (
      <div className="p-4 bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-2xl border border-green-200 dark:border-green-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
            <CheckCircle className="text-green-600 dark:text-green-400" size={20} />
          </div>
          <div className="flex-1">
            <p className="font-medium text-green-800 dark:text-green-300">Order Confirmed!</p>
            <p className="text-sm text-green-600 dark:text-green-400">{order.medicine_name} × {order.quantity}</p>
          </div>
          <p className="font-semibold text-green-700 dark:text-green-300">₹{order.total_price}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div 
        className={`w-full max-w-md bg-white dark:bg-slate-800 rounded-3xl shadow-2xl overflow-hidden transform transition-all duration-500 ${
          isVisible ? 'scale-100 opacity-100' : 'scale-90 opacity-0'
        }`}
      >
        {/* Success Animation Header */}
        <div className="relative bg-gradient-to-r from-green-500 to-teal-500 p-6 text-center">
          <div className={`flex justify-center mb-4 transform transition-all duration-500 ${
            animateStep >= 1 ? 'scale-100 opacity-100' : 'scale-0 opacity-0'
          }`}>
            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-lg">
              <CheckCircle className="text-green-500" size={40} />
            </div>
          </div>
          <h2 className={`text-2xl font-bold text-white transition-all duration-500 ${
            animateStep >= 2 ? 'opacity-100' : 'opacity-0'
          }`}>
            Order Confirmed!
          </h2>
          <p className={`text-green-100 mt-1 transition-all duration-500 ${
            animateStep >= 2 ? 'opacity-100' : 'opacity-0'
          }`}>
            Thank you for your order
          </p>
          
          {/* Close button */}
          {onClose && (
            <button
              onClick={onClose}
              className="absolute top-4 right-4 w-8 h-8 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-colors"
            >
              <X className="text-white" size={16} />
            </button>
          )}
        </div>

        {/* Order Details */}
        <div className="p-6 space-y-4">
          {/* Order ID */}
          <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700">
            <span className="text-sm text-slate-500 dark:text-slate-400">Order ID</span>
            <span className="font-mono font-medium text-slate-900 dark:text-white">#{order.order_id}</span>
          </div>

          {/* Medicine Details */}
          <div className="py-2 border-b border-slate-100 dark:border-slate-700">
            <span className="text-sm text-slate-500 dark:text-slate-400">Medicine</span>
            <p className="font-medium text-slate-900 dark:text-white">{order.medicine_name}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              ₹{order.unit_price} × {order.quantity} units
            </p>
          </div>

          {/* Total */}
          <div className="flex items-center justify-between py-2">
            <span className="text-lg font-medium text-slate-700 dark:text-slate-300">Total Amount</span>
            <span className="text-2xl font-bold text-teal-600 dark:text-teal-400">₹{order.total_price}</span>
          </div>

          {/* Status Timeline */}
          <div className={`mt-6 transition-all duration-500 ${
            animateStep >= 3 ? 'opacity-100' : 'opacity-0'
          }`}>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-3">Order Status</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-green-100 dark:bg-green-900/30 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-teal-500 rounded-full transition-all duration-1000"
                  style={{ width: order.status === 'delivered' ? '100%' : '60%' }}
                />
              </div>
              <div className="flex items-center gap-1">
                {getStatusIcon()}
                <span className="text-sm font-medium text-green-700 dark:text-green-300">
                  {getStatusText()}
                </span>
              </div>
            </div>
          </div>

          {/* Estimated Delivery */}
          {order.estimated_delivery && (
            <div className={`flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-xl transition-all duration-500 ${
              animateStep >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}>
              <Clock className="text-blue-500 flex-shrink-0" size={20} />
              <div>
                <p className="text-xs text-blue-500 dark:text-blue-400 font-medium">Estimated Delivery</p>
                <p className="text-sm text-blue-700 dark:text-blue-300">{order.estimated_delivery}</p>
              </div>
            </div>
          )}

          {/* Delivery Address */}
          {order.delivery_address && (
            <div className={`flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl transition-all duration-500 ${
              animateStep >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}>
              <MapPin className="text-slate-500 flex-shrink-0 mt-0.5" size={18} />
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Delivery Address</p>
                <p className="text-sm text-slate-700 dark:text-slate-300">{order.delivery_address}</p>
              </div>
            </div>
          )}

          {/* Email Confirmation */}
          {order.customer_email && (
            <div className={`flex items-center gap-3 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-xl transition-all duration-500 ${
              animateStep >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}>
              <Mail className="text-purple-500 flex-shrink-0" size={18} />
              <div>
                <p className="text-xs text-purple-500 dark:text-purple-400 font-medium">Confirmation Email Sent</p>
                <p className="text-sm text-purple-700 dark:text-purple-300">{order.customer_email}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-700">
          <p className="text-xs text-center text-slate-500 dark:text-slate-400">
            Need help? Contact us at support@swasthyasarthi.com
          </p>
        </div>
      </div>
    </div>
  );
}

// Compact Order Status Badge
export function OrderStatusBadge({ status }: { status: OrderDetails['status'] }) {
  const statusConfig = {
    confirmed: { color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400', icon: CheckCircle, label: 'Confirmed' },
    processing: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400', icon: Package, label: 'Processing' },
    shipped: { color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400', icon: Truck, label: 'Shipped' },
    delivered: { color: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400', icon: CheckCircle, label: 'Delivered' },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}>
      <Icon size={12} />
      {config.label}
    </span>
  );
}
