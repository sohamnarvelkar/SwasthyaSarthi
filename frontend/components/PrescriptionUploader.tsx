/**
 * PrescriptionUploader Component
 * Allows users to upload prescription images for automatic medicine detection
 * 
 * Features:
 * - Drag & drop upload
 * - Camera capture (mobile)
 * - Image preview
 * - Upload progress indicator
 * - Supports jpg, jpeg, png, pdf
 */

'use client';

import { useState, useRef, useCallback } from 'react';

interface DetectedMedicine {
  name: string;
  matched_dataset_name: string;
  confidence: number;
  is_high_confidence: boolean;
}

interface PrescriptionResult {
  success: boolean;
  detected_medicines: DetectedMedicine[];
  unmatched_medicines: string[];
  message: string;
  prescription_image: string;
  ocr_confidence: number;
}

interface PrescriptionUploaderProps {
  onMedicinesDetected?: (medicines: DetectedMedicine[]) => void;
  onOrderConfirm?: (medicines: DetectedMedicine[]) => void;
  onError?: (error: string) => void;
}

export default function PrescriptionUploader({
  onMedicinesDetected,
  onOrderConfirm,
  onError
}: PrescriptionUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<PrescriptionResult | null>(null);
  const [selectedMedicines, setSelectedMedicines] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Default to English - language can be passed as prop if needed
  const language = 'en';

  // Handle drag events
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && validateFile(droppedFile)) {
      handleFileSelection(droppedFile);
    }
  }, []);

  // Validate file type
  const validateFile = (file: File): boolean => {
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
      setError('Invalid file type. Please upload jpg, jpeg, png, or pdf.');
      return false;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum size is 10MB.');
      return false;
    }
    return true;
  };

  // Handle file selection
  const handleFileSelection = (selectedFile: File) => {
    setError(null);
    setResult(null);
    setFile(selectedFile);
    setSelectedMedicines(new Set());
    
    // Create preview
    if (selectedFile.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(selectedFile);
    } else {
      setPreview(null);
    }
  };

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      handleFileSelection(selectedFile);
    }
  };

  // Handle camera capture
  const handleCameraCapture = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment';
    input.onchange = (e) => {
      const selectedFile = (e.target as HTMLInputElement).files?.[0];
      if (selectedFile && validateFile(selectedFile)) {
        handleFileSelection(selectedFile);
      }
    };
    input.click();
  };

  // Upload prescription
  const uploadPrescription = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // Map frontend language to backend language code
      const langMap: Record<string, string> = {
        'en': 'en',
        'hi': 'hi',
        'mr': 'mr'
      };
      formData.append('language', langMap[language] || 'en');

      const xhr = new XMLHttpRequest();
      
      // Progress tracking
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setProgress(percent);
        }
      };

      // Wait for completion
      await new Promise<void>((resolve, reject) => {
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error(`Upload failed: ${xhr.status}`));
          }
        };
        xhr.onerror = () => reject(new Error('Upload failed'));
        xhr.open('POST', '/analyze-prescription');
        xhr.send(formData);
      });

      // Get response
      const response = await fetch('/analyze-prescription', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to analyze prescription');
      }

      const data: PrescriptionResult = await response.json();
      setResult(data);
      
      // Auto-select all high-confidence medicines
      const highConfidence = data.detected_medicines
        .filter(m => m.is_high_confidence)
        .map(m => m.matched_dataset_name);
      setSelectedMedicines(new Set(highConfidence));
      
      // Notify parent
      if (data.detected_medicines.length > 0) {
        onMedicinesDetected?.(data.detected_medicines);
      }
      
      if (!data.success) {
        setError(data.message);
        onError?.(data.message);
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to upload prescription';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  // Toggle medicine selection
  const toggleMedicine = (medicineName: string) => {
    const newSelected = new Set(selectedMedicines);
    if (newSelected.has(medicineName)) {
      newSelected.delete(medicineName);
    } else {
      newSelected.add(medicineName);
    }
    setSelectedMedicines(newSelected);
  };

  // Confirm order
  const handleConfirmOrder = () => {
    if (!result) return;
    
    const selectedMeds = result.detected_medicines.filter(
      m => selectedMedicines.has(m.matched_dataset_name)
    );
    
    if (selectedMeds.length > 0) {
      onOrderConfirm?.(selectedMeds);
    }
  };

  // Clear/reset
  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setSelectedMedicines(new Set());
    setError(null);
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          📝 Upload Prescription
        </h2>
        
        {/* Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {preview ? (
            <div className="space-y-4">
              <img 
                src={preview} 
                alt="Prescription preview" 
                className="max-h-48 mx-auto rounded-lg"
              />
              <p className="text-sm text-gray-600">{file?.name}</p>
            </div>
          ) : (
            <>
              <div className="text-4xl mb-4">📄</div>
              <p className="text-gray-600 mb-2">
                Drag & drop your prescription here
              </p>
              <p className="text-sm text-gray-500 mb-4">
                or
              </p>
              <div className="flex gap-2 justify-center">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Browse Files
                </button>
                <button
                  onClick={handleCameraCapture}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  📷 Take Photo
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-4">
                Supported: JPG, JPEG, PNG, PDF (max 10MB)
              </p>
            </>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/jpg,application/pdf"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        {/* Progress Bar */}
        {uploading && (
          <div className="mt-4">
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-1 text-center">
              Analyzing prescription... {progress}%
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">⚠️ {error}</p>
          </div>
        )}

        {/* Results */}
        {result && result.success && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-2 text-green-600">
              <span className="text-xl">✅</span>
              <span className="font-semibold">Prescription Processed</span>
            </div>
            
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-4 py-2 border-b">
                <h3 className="font-medium text-gray-700">
                  Detected Medicines:
                </h3>
              </div>
              
              <div className="divide-y">
                {result.detected_medicines.map((med, index) => (
                  <div 
                    key={index}
                    className={`p-3 flex items-center justify-between ${
                      selectedMedicines.has(med.matched_dataset_name)
                        ? 'bg-blue-50'
                        : 'bg-white'
                    }`}
                  >
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedMedicines.has(med.matched_dataset_name)}
                        onChange={() => toggleMedicine(med.matched_dataset_name)}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <div>
                        <p className="font-medium text-gray-800">
                          {med.matched_dataset_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {med.name} • {Math.round(med.confidence * 100)}% match
                        </p>
                      </div>
                    </label>
                    <span className={`text-xs px-2 py-1 rounded ${
                      med.is_high_confidence 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {med.is_high_confidence ? '✓ High' : '○ Medium'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Unmatched Medicines */}
            {result.unmatched_medicines.length > 0 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-700">
                  ⚠️ Could not match: {result.unmatched_medicines.join(', ')}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleConfirmOrder}
                disabled={selectedMedicines.size === 0}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                  selectedMedicines.size > 0
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Confirm Order ({selectedMedicines.size})
              </button>
              <button
                onClick={handleClear}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        )}

        {/* Clear Button when file selected but not uploaded */}
        {file && !result && !uploading && (
          <div className="mt-4 flex gap-3">
            <button
              onClick={uploadPrescription}
              className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              🔍 Analyze Prescription
            </button>
            <button
              onClick={handleClear}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
