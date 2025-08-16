'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, FileText, MessageCircle } from 'lucide-react';
import FileUpload from '@/components/FileUpload';
import DataVisualization from '@/components/DataVisualization';
import Chat from '@/components/Chat';
import { FileUploadResponse } from '@/types';

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState<FileUploadResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'analysis' | 'chat'>('upload');

  const handleFileUploaded = (response: FileUploadResponse) => {
    setUploadedFile(response);
    setActiveTab('analysis');
  };

  const tabs = [
    { id: 'upload', label: 'Upload File', icon: FileText },
    { id: 'analysis', label: 'Analysis', icon: BarChart3, disabled: !uploadedFile },
    { id: 'chat', label: 'Chat', icon: MessageCircle, disabled: !uploadedFile },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Data Assistant</h1>
              <p className="text-gray-600">Upload, analyze, and chat with your data</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">API Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              const isDisabled = tab.disabled;

              return (
                <button
                  key={tab.id}
                  onClick={() => !isDisabled && setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    isActive
                      ? 'border-blue-500 text-blue-600'
                      : isDisabled
                      ? 'border-transparent text-gray-400 cursor-not-allowed'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                  disabled={isDisabled}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Welcome to Data Assistant
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Upload your data files (CSV, Excel, PDF, Word) and let our AI 
                analyze them. Then chat with your data to get insights and answers.
              </p>
            </div>
            <FileUpload onFileUploaded={handleFileUploaded} />
          </motion.div>
        )}

        {activeTab === 'analysis' && uploadedFile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Descriptive Analysis Results</h2>
              <p className="text-gray-600">Here's what we found in your data</p>
            </div>
            <DataVisualization fileData={uploadedFile} />
            <div className="text-center">
              <button
                onClick={() => setActiveTab('chat')}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Start Chatting with Your Data
              </button>
            </div>
          </motion.div>
        )}

        {activeTab === 'chat' && uploadedFile && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Chat with Your Data</h2>
              <p className="text-gray-600">Ask questions and get AI-powered insights</p>
            </div>
            <Chat fileId={uploadedFile.file_id} filename={uploadedFile.filename} />
          </motion.div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>© 2025 Data Assistant. Built with Next.js, FastAPI, and Gemini AI.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}