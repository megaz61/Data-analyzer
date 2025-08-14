'use client';

import { motion } from 'framer-motion';
import { FileUploadResponse } from '@/types';

// Dynamic imports for chart.js components to avoid SSR issues.
// Install these with: npm install react-chartjs-2 chart.js
import dynamic from 'next/dynamic';
const Bar = dynamic(() => import('react-chartjs-2').then((mod) => mod.Bar), { ssr: false });
const Line = dynamic(() => import('react-chartjs-2').then((mod) => mod.Line), { ssr: false });

// Register chart.js components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

interface DataVisualizationProps {
  fileData: FileUploadResponse;
}

export default function DataVisualization({ fileData }: DataVisualizationProps) {
  const { analysis_summary } = fileData;

  // Render charts from analysis_summary.charts
  const renderCharts = () => {
    if (!analysis_summary?.charts) return null;
    const chartEntries = Object.entries(analysis_summary.charts);
    if (chartEntries.length === 0) return null;

    return chartEntries.map(([colName, chartInfo]: any, idx: number) => {
      const { type } = chartInfo;
      if (type === 'histogram') {
        const bins: number[] = chartInfo.bins;
        const counts: number[] = chartInfo.counts;
        const labels = [] as string[];
        for (let i = 0; i < bins.length - 1; i++) {
          const mid = (bins[i] + bins[i + 1]) / 2;
          labels.push(mid.toFixed(2));
        }
        const data = {
          labels,
          datasets: [
            {
              label: colName,
              data: counts,
              backgroundColor: 'rgba(54, 162, 235, 0.5)',
              borderColor: 'rgba(54, 162, 235, 1)',
              borderWidth: 1,
            },
          ],
        };
        const options = {
          responsive: true,
          plugins: {
            legend: { display: false },
            title: { display: true, text: `Distribution of ${colName}` },
          },
          scales: {
            x: {
              title: { display: true, text: colName },
              ticks: { maxTicksLimit: 10 },
            },
            y: {
              title: { display: true, text: 'Count' },
            },
          },
        };
        return (
          <div key={idx} className="bg-white border rounded-lg p-4 shadow-sm">
            <Bar data={data} options={options as any} />
          </div>
        );
      } else if (type === 'bar') {
        const labels: string[] = chartInfo.categories;
        const counts: number[] = chartInfo.counts;
        const data = {
          labels,
          datasets: [
            {
              label: colName,
              data: counts,
              backgroundColor: 'rgba(75, 192, 192, 0.5)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1,
            },
          ],
        };
        const options = {
          responsive: true,
          plugins: {
            legend: { display: false },
            title: { display: true, text: `Top categories in ${colName}` },
          },
          scales: {
            x: {
              title: { display: true, text: colName },
              ticks: { maxTicksLimit: 10 },
            },
            y: {
              title: { display: true, text: 'Count' },
            },
          },
        };
        return (
          <div key={idx} className="bg-white border rounded-lg p-4 shadow-sm">
            <Bar data={data} options={options as any} />
          </div>
        );
      }
      return null;
    });
  };

  // Render summary and charts
  const renderAnalysis = () => {
    if (!analysis_summary) return null;

    return (
      <div className="space-y-4">
        {analysis_summary.shape && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Dataset Shape</h4>
            <p className="text-blue-800">
              Rows: {analysis_summary.shape[0]}, Columns: {analysis_summary.shape[1]}
            </p>
          </div>
        )}

        {analysis_summary.columns && (
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-semibold text-green-900 mb-2">Columns</h4>
            <div className="flex flex-wrap gap-2">
              {analysis_summary.columns.map((col: string, idx: number) => (
                <span key={idx} className="px-2 py-1 bg-green-200 text-green-800 text-sm rounded">
                  {col}
                </span>
              ))}
            </div>
          </div>
        )}

        {analysis_summary.word_count && (
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-semibold text-purple-900 mb-2">Document Info</h4>
            <p className="text-purple-800">
              Word Count: {analysis_summary.word_count} | Character Count: {analysis_summary.char_count}
            </p>
          </div>
        )}

        {analysis_summary.total_sheets && (
          <div className="bg-orange-50 p-4 rounded-lg">
            <h4 className="font-semibold text-orange-900 mb-2">Excel File Info</h4>
            <p className="text-orange-800">
              Sheets: {analysis_summary.total_sheets} | Total Rows: {analysis_summary.total_rows}
            </p>
          </div>
        )}

        {/* Render charts if available */}
        {analysis_summary.charts && (
          <div className="space-y-6 mt-6">
            <h4 className="text-lg font-semibold text-gray-900">Data Visualizations</h4>
            <p className="text-sm text-gray-600 mb-2">
              Automatically generated charts based on your data.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {renderCharts()}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-4xl mx-auto p-6"
    >
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-gray-900 mb-2">File Analysis</h3>
          <p className="text-gray-600">Filename: {fileData.filename}</p>
          <p className="text-gray-600">File ID: {fileData.file_id}</p>
        </div>
        {renderAnalysis()}
      </div>
    </motion.div>
  );
}
