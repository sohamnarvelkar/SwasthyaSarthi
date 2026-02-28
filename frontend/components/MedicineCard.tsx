'use client';

import React, { useState } from 'react';
import { Pill, Package, DollarSign, AlertTriangle, ShoppingCart, Check } from 'lucide-react';

export interface Medicine {
  id: string;
  name: string;
  description: string;
  package_size: string;
  price: number;
  in_stock: boolean;
  dosage?: string;
  warnings?: string[];
}

interface MedicineCardProps {
  medicine: Medicine;
  onOrder?: (medicine: Medicine, quantity: number) => void;
  compact?: boolean;
}

export function MedicineCard({ medicine, onOrder, compact = false }: MedicineCardProps) {
  const [quantity, setQuantity] = useState(1);
  const [isOrdering, setIsOrdering] = useState(false);
  const [ordered, setOrdered] = useState(false);

  const handleOrder = async () => {
    if (!onOrder || !medicine.in_stock) return;
    
    setIsOrdering(true);
    try {
      await onOrder(medicine, quantity);
      setOrdered(true);
      setTimeout(() => setOrdered(false), 3000);
    } catch (error) {
      console.error('Order failed:', error);
    } finally {
      setIsOrdering(false);
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow">
        <div className="w-10 h-10 bg-teal-100 dark:bg-teal-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
          <Pill size={20} className="text-teal-600 dark:text-teal-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-slate-900 dark:text-white truncate">{medicine.name}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400">{medicine.package_size}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="font-semibold text-teal-600 dark:text-teal-400">₹{medicine.price}</p>
          <p className={`text-xs ${medicine.in_stock ? 'text-green-500' : 'text-red-500'}`}>
            {medicine.in_stock ? 'In Stock' : 'Out of Stock'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20 border-b border-slate-100 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-blue-500 rounded-xl flex items-center justify-center">
            <Pill size={24} className="text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-slate-900 dark:text-white">{medicine.name}</h3>
            <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
              <Package size={14} />
              <span>{medicine.package_size}</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-teal-600 dark:text-teal-400">₹{medicine.price}</p>
            <p className={`text-xs font-medium ${medicine.in_stock ? 'text-green-500' : 'text-red-500'}`}>
              {medicine.in_stock ? '✓ In Stock' : '✗ Out of Stock'}
            </p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-4">
        {/* Description */}
        <p className="text-sm text-slate-600 dark:text-slate-300">{medicine.description}</p>

        {/* Dosage */}
        {medicine.dosage && (
          <div className="flex items-start gap-2 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
            <Pill size={16} className="text-blue-500 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Dosage</p>
              <p className="text-sm text-slate-700 dark:text-slate-300">{medicine.dosage}</p>
            </div>
          </div>
        )}

        {/* Warnings */}
        {medicine.warnings && medicine.warnings.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase flex items-center gap-1">
              <AlertTriangle size={12} className="text-amber-500" />
              Safety Warnings
            </p>
            <ul className="space-y-1">
              {medicine.warnings.map((warning, index) => (
                <li key={index} className="text-xs text-amber-700 dark:text-amber-300 flex items-start gap-1">
                  <span className="mt-1 w-1 h-1 bg-amber-500 rounded-full flex-shrink-0" />
                  {warning}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Order Section */}
        {medicine.in_stock && onOrder && (
          <div className="flex items-center gap-3 pt-2 border-t border-slate-100 dark:border-slate-700">
            {/* Quantity Selector */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-8 h-8 flex items-center justify-center bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                disabled={quantity <= 1}
              >
                -
              </button>
              <span className="w-8 text-center font-medium text-slate-700 dark:text-slate-300">{quantity}</span>
              <button
                onClick={() => setQuantity(Math.min(10, quantity + 1))}
                className="w-8 h-8 flex items-center justify-center bg-slate-100 dark:bg-slate-700 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                disabled={quantity >= 10}
              >
                +
              </button>
            </div>

            {/* Total Price */}
            <div className="flex-1">
              <p className="text-xs text-slate-500 dark:text-slate-400">Total</p>
              <p className="font-semibold text-slate-900 dark:text-white">₹{medicine.price * quantity}</p>
            </div>

            {/* Order Button */}
            <button
              onClick={handleOrder}
              disabled={isOrdering || ordered}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium transition-all ${
                ordered
                  ? 'bg-green-500 text-white'
                  : 'bg-teal-500 hover:bg-teal-600 text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isOrdering ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : ordered ? (
                <>
                  <Check size={18} />
                  <span>Ordered!</span>
                </>
              ) : (
                <>
                  <ShoppingCart size={18} />
                  <span>Order Now</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Medicine List Component
interface MedicineListProps {
  medicines: Medicine[];
  onOrder?: (medicine: Medicine, quantity: number) => void;
}

export function MedicineList({ medicines, onOrder }: MedicineListProps) {
  return (
    <div className="space-y-3">
      {medicines.map((medicine) => (
        <MedicineCard key={medicine.id} medicine={medicine} onOrder={onOrder} />
      ))}
    </div>
  );
}
