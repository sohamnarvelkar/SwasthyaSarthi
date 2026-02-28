'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Sidebar } from '@/components/Sidebar';
import { MedicineCard, Medicine } from '@/components/MedicineCard';
import { getMedicines, MedicineData } from '@/services/api';
import { Search, Filter, Pill, Package, DollarSign, AlertCircle, Loader2 } from 'lucide-react';

function MedicinesPage() {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [filteredMedicines, setFilteredMedicines] = useState<Medicine[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [stockFilter, setStockFilter] = useState('all');
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    loadMedicines();
  }, []);

  useEffect(() => {
    filterMedicines();
  }, [medicines, searchTerm, categoryFilter, stockFilter]);

  const loadMedicines = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getMedicines();
      
      // Transform data to match MedicineCard interface
      const transformedMedicines: Medicine[] = data.map((med: MedicineData) => ({
        id: med.id.toString(),
        name: med.name,
        description: med.description || '',
        package_size: med.package_size || '',
        price: med.price || 0,
        in_stock: med.in_stock ?? true,
        dosage: med.dosage,
        warnings: med.warnings ? [med.warnings] : undefined,
      }));
      
      setMedicines(transformedMedicines);
      
      // Extract unique categories
      const categorySet = new Set<string>();
      data.forEach((med: MedicineData) => {
        if (med.category) categorySet.add(med.category);
      });
      setCategories(Array.from(categorySet));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load medicines');
    } finally {
      setIsLoading(false);
    }
  };

  const filterMedicines = () => {
    let filtered = [...medicines];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (med) =>
          med.name.toLowerCase().includes(term) ||
          med.description.toLowerCase().includes(term)
      );
    }

    // Category filter (only if category exists on the medicine)
    if (categoryFilter !== 'all') {
      filtered = filtered.filter((med) => (med as any).category === categoryFilter);
    }

    // Stock filter
    if (stockFilter === 'in_stock') {
      filtered = filtered.filter((med) => med.in_stock);
    } else if (stockFilter === 'out_of_stock') {
      filtered = filtered.filter((med) => !med.in_stock);
    }

    setFilteredMedicines(filtered);
  };

  const handleOrder = async (medicine: Medicine, quantity: number) => {
    console.log('Ordering:', medicine.name, 'Quantity:', quantity);
    // Add order logic here
  };

  return (
    <div className="flex h-screen bg-white dark:bg-slate-900">
      <Sidebar
        conversations={[]}
        activeConversationId={null}
        onSelectConversation={() => {}}
        onNewConversation={() => {}}
        onDeleteConversation={() => {}}
        isVoiceMode={false}
        onToggleVoiceMode={() => {}}
        isDarkMode={false}
        onToggleDarkMode={() => {}}
        userEmail=""
        onLogout={() => {}}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Pill className="text-teal-500" />
                Medicine Database
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mt-1">
                Browse and search our complete medicine catalog
              </p>
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">
              {filteredMedicines.length} of {medicines.length} medicines
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="text"
                  placeholder="Search medicines..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>
            </div>

            {/* Category Filter */}
            <div className="flex items-center gap-2">
              <Filter size={18} className="text-slate-400" />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="all">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Stock Filter */}
            <select
              value={stockFilter}
              onChange={(e) => setStockFilter(e.target.value)}
              className="px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="all">All Stock</option>
              <option value="in_stock">In Stock</option>
              <option value="out_of_stock">Out of Stock</option>
            </select>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="animate-spin text-teal-500" size={48} />
              <span className="ml-3 text-slate-500 dark:text-slate-400">Loading medicines...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <AlertCircle className="text-red-500 mb-4" size={48} />
              <p className="text-red-500 dark:text-red-400">{error}</p>
              <button
                onClick={loadMedicines}
                className="mt-4 px-4 py-2 bg-teal-500 text-white rounded-xl hover:bg-teal-600 transition-colors"
              >
                Retry
              </button>
            </div>
          ) : filteredMedicines.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <Pill className="text-slate-300 dark:text-slate-600 mb-4" size={48} />
              <p className="text-slate-500 dark:text-slate-400">No medicines found</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredMedicines.map((medicine) => (
                <MedicineCard
                  key={medicine.id}
                  medicine={medicine}
                  onOrder={handleOrder}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <MedicinesPage />
    </ProtectedRoute>
  );
}
