'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, CheckCircle, AlertCircle, FileSpreadsheet, FileText, File } from 'lucide-react';
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
  const [fileDetection, setFileDetection] = useState<any>(null);

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'csv':
        return <FileSpreadsheet className="w-8 h-8 text-green-600" />;
      case 'xlsx':
      case 'xls':
        return <FileSpreadsheet className="w-8 h-8 text-blue-600" />;
      case 'pdf':
        return <FileText className="w-8 h-8 text-red-600" />;
      default:
        return <File className="w-8 h-8 text-gray-600" />;
    }
  };

  const onDrop = useCallback(async (acceptedFiles: globalThis.File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadStatus('idle');
    setErrorMessage('');
    setFileDetection(null);

    try {
      const response = await uploadFile(file);
      setUploadStatus('success');
      setFileDetection(response.file_detection);
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
      'application/pdf': ['.pdf']
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
            <p className="text-sm text-gray-400">Analyzing content and structure...</p>
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
                <div className="flex justify-center space-x-4 mb-4">
                  <div className="flex items-center space-x-1 text-xs text-gray-400">
                    <FileSpreadsheet className="w-4 h-4 text-green-600" />
                    <span>CSV</span>
                  </div>
                  <div className="flex items-center space-x-1 text-xs text-gray-400">
                    <FileSpreadsheet className="w-4 h-4 text-blue-600" />
                    <span>Excel</span>
                  </div>
                  <div className="flex items-center space-x-1 text-xs text-gray-400">
                    <FileText className="w-4 h-4 text-red-600" />
                    <span>PDF</span>
                  </div>
                </div>
                <p className="text-xs text-gray-400">
                  Supported formats: CSV, Excel (.xlsx, .xls), PDF
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
          className="mt-4 space-y-4"
        >
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="text-green-800">File uploaded and processed successfully!</span>
          </div>
          
          {fileDetection && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2 flex items-center space-x-2">
                {getFileIcon(fileDetection.filename)}
                <span>File Detection Results</span>
              </h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-500">File Type:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {fileDetection.extension?.toUpperCase()} ({fileDetection.type})
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">File Size:</span>
                  <span className="ml-2 font-medium text-gray-900">{fileDetection.size_mb} MB</span>
                </div>
                {fileDetection.type === 'csv' && (
                  <>
                    <div>
                      <span className="text-gray-500">Encoding:</span>
                      <span className="ml-2 font-medium text-gray-900">{fileDetection.encoding}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Delimiter:</span>
                      <span className="ml-2 font-medium text-gray-900">"{fileDetection.delimiter}"</span>
                    </div>
                  </>
                )}
                {fileDetection.type === 'excel' && (
                  <>
                    <div>
                      <span className="text-gray-500">Sheets:</span>
                      <span className="ml-2 font-medium text-gray-900">{fileDetection.sheet_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Estimated Rows:</span>
                      <span className="ml-2 font-medium text-gray-900">{fileDetection.estimated_rows}</span>
                    </div>
                  </>
                )}
                {fileDetection.type === 'pdf' && (
                  <>
                    <div>
                      <span className="text-gray-500">Pages:</span>
                      <span className="ml-2 font-medium text-gray-900">{fileDetection.page_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Text Extractable:</span>
                      <span className="ml-2 font-medium text-gray-900">
                        {fileDetection.estimated_extractable ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
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