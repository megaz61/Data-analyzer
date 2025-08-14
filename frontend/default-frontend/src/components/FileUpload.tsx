'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadFile } from '@/lib/api';
import type { FileUploadResponse } from '@/types';
import LoadingSpinner from './LoadingSpinner';

interface FileUploadProps {
  onFileUploaded: (response: FileUploadResponse) => void;
}

export default function FileUpload({ onFileUploaded }: FileUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const onDrop = useCallback(async (acceptedFiles: globalThis.File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadStatus('idle');
    setErrorMessage('');

    try {
      const response = await uploadFile(file);
      setUploadStatus('success');
      onFileUploaded(response);
    } catch (error: any) {
      setUploadStatus('error');
      setErrorMessage(error?.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  });

  const rootClass = `
    border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
    ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
    ${uploading ? 'pointer-events-none opacity-50' : ''}
  `;

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <motion.div
        {...getRootProps({ className: rootClass })}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <input {...getInputProps()} />

        {uploading ? (
          <div className="flex flex-col items-center space-y-4">
            <LoadingSpinner />
            <p className="text-gray-600">Processing your file...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-blue-100 rounded-full">
              <Upload className="w-8 h-8 text-blue-600" />
            </div>

            {isDragActive ? (
              <p className="text-lg text-blue-600">Drop the file here...</p>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drag &amp; drop your file here
                </p>
                <p className="text-sm text-gray-500 mb-4">or click to select a file</p>
                <p className="text-xs text-gray-400">
                  Supported formats: CSV, Excel, PDF, Word, TXT
                </p>
              </div>
            )}
          </div>
        )}
      </motion.div>

      {uploadStatus === 'success' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-3"
        >
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-800">File uploaded and processed successfully!</span>
        </motion.div>
      )}

      {uploadStatus === 'error' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3"
        >
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-800">{errorMessage}</span>
        </motion.div>
      )}
    </div>
  );
}