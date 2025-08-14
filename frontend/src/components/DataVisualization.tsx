import React from 'react';
import {
  FileSpreadsheet,
  FileText,
  BarChart3 as BarChartIcon,
  PieChart as PieChartIcon,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Info,
  Clock,
  Database,
  Eye,
  Activity,
  Target,
  BarChart2,
} from 'lucide-react';

// Recharts
import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Cell
} from 'recharts';

import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  ScatterChart,
  Scatter
} from 'recharts';

interface DataVisualizationProps {
  fileData: {
    filename: string;
    file_id: string;
    type: 'csv' | 'excel' | 'pdf' | string;
    file_detection?: any;
    analysis_summary?: any;
    data?: any;
  };
}

const DataVisualization: React.FC<DataVisualizationProps> = ({ fileData }) => {
  const { analysis_summary, file_detection } = fileData || {};

  // For Excel files, get analysis from the first sheet if analysis_summary doesn't have detailed info
  const getAnalysisData = () => {
    if (fileData?.type === 'excel' && fileData.data) {
      const firstSheetName = Object.keys(fileData.data)[0];
      if (firstSheetName && fileData.data[firstSheetName]?.analysis) {
        return fileData.data[firstSheetName].analysis;
      }
    }
    return analysis_summary;
  };

  const analysisData = getAnalysisData();

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getQualityIcon = (score: number) => {
    if (score >= 80) return <CheckCircle className="w-5 h-5" />;
    if (score >= 60) return <AlertTriangle className="w-5 h-5" />;
    return <AlertTriangle className="w-5 h-5" />;
  };

  // Palette untuk chart
  const chartColors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1',
    '#d084d0', '#ffb347', '#87ceeb', '#dda0dd', '#98fb98'
  ];

  // === File detection ===
  const renderFileDetection = () => {
    if (!file_detection) return null;

    return (
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-3 flex items-center space-x-2">
          <Info className="w-5 h-5" />
          <span>File Detection & Analysis</span>
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div>
            <span className="text-blue-600">Type:</span>
            <span className="ml-2 font-medium text-blue-900">
              {file_detection.type?.toUpperCase()}
            </span>
          </div>
          <div>
            <span className="text-blue-600">Size:</span>
            <span className="ml-2 font-medium text-blue-900">{file_detection.size_mb} MB</span>
          </div>

          {file_detection.type === 'csv' && (
            <>
              <div>
                <span className="text-blue-600">Encoding:</span>
                <span className="ml-2 font-medium text-blue-900">{file_detection.encoding}</span>
              </div>
              <div>
                <span className="text-blue-600">Delimiter:</span>
                <span className="ml-2 font-medium text-blue-900">"{file_detection.delimiter}"</span>
              </div>
            </>
          )}

          {file_detection.type === 'excel' && (
            <>
              <div>
                <span className="text-blue-600">Sheets:</span>
                <span className="ml-2 font-medium text-blue-900">{file_detection.sheet_count}</span>
              </div>
              <div>
                <span className="text-blue-600">Engine:</span>
                <span className="ml-2 font-medium text-blue-900">{file_detection.engine}</span>
              </div>
            </>
          )}

          {file_detection.type === 'pdf' && (
            <>
              <div>
                <span className="text-blue-600">Pages:</span>
                <span className="ml-2 font-medium text-blue-900">{file_detection.page_count}</span>
              </div>
              <div>
                <span className="text-blue-600">Extractable:</span>
                <span className="ml-2 font-medium text-blue-900">
                  {file_detection.estimated_extractable ? 'Yes' : 'No'}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  // === Column types ===
  const renderColumnTypes = () => {
    const columnTypes = analysisData?.column_types;
    if (!columnTypes) return null;

    const typeColors: Record<string, string> = {
      'integer': 'bg-blue-100 text-blue-800',
      'float': 'bg-purple-100 text-purple-800',
      'text': 'bg-gray-100 text-gray-800',
      'categorical': 'bg-green-100 text-green-800',
      'datetime': 'bg-orange-100 text-orange-800',
      'boolean': 'bg-pink-100 text-pink-800',
      'email': 'bg-indigo-100 text-indigo-800',
      'url': 'bg-cyan-100 text-cyan-800',
      'phone': 'bg-teal-100 text-teal-800',
      'empty': 'bg-gray-100 text-gray-800'
    };

    return (
      <div className="bg-white border rounded-lg p-4 shadow-sm">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Database className="w-5 h-5" />
          <span>Column Type Detection</span>
        </h4>
        <div className="grid gap-3">
          {Object.entries(columnTypes).map(([column, info]: [string, any]) => (
            <div key={column} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex-1">
                <span className="font-medium text-gray-900">{column}</span>
                <div className="flex items-center space-x-2 mt-1">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      typeColors[info.detected_type as keyof typeof typeColors] || 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {info.detected_type}
                  </span>
                  {'confidence' in info && (
                    <span className="text-xs text-gray-500">{info.confidence}% confidence</span>
                  )}
                </div>
              </div>
              <div className="text-right text-sm text-gray-600">
                {'null_percentage' in info && <div>Nulls: {info.null_percentage}%</div>}
                {'unique_count' in info && <div>Unique: {info.unique_count}</div>}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // === Data quality ===
  const renderDataQuality = () => {
    const quality = analysisData?.data_quality;
    if (!quality) return null;

    const score = quality.data_quality_score || 0;

    return (
      <div className={`p-4 rounded-lg border ${getQualityColor(score)}`}>
        <h4 className="font-semibold mb-3 flex items-center space-x-2">
          {getQualityIcon(score)}
          <span>Data Quality Assessment</span>
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="font-medium">Overall Score</div>
            <div className="text-lg font-bold">{score}/100</div>
          </div>
          <div>
            <div className="font-medium">Completeness</div>
            <div>{quality.completeness_percentage}%</div>
          </div>
          <div>
            <div className="font-medium">Duplicates</div>
            <div>
              {quality.duplicate_rows} rows ({quality.duplicate_percentage}%)
            </div>
          </div>
          <div>
            <div className="font-medium">High Null Columns</div>
            <div>{quality.high_null_columns?.length || 0}</div>
          </div>
        </div>

        {quality.high_null_columns?.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            <div className="text-sm font-medium mb-2">Columns with &gt; 50% missing data:</div>
            <div className="flex flex-wrap gap-2">
              {quality.high_null_columns.map((col: any, idx: number) => (
                <span key={idx} className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">
                  {col.column} ({col.null_percentage}%)
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // === PDF statistics - FIXED VERSION ===
  const renderPDFStats = () => {
    // Debug logs untuk troubleshooting
    console.log('=== PDF STATS DEBUG ===');
    console.log('fileData.type:', fileData?.type);
    console.log('file_detection.type:', file_detection?.type);
    console.log('analysis_summary exists:', !!analysis_summary);

    // Return null jika tidak ada analysis_summary
    if (!analysis_summary) {
      console.log('No analysis_summary, returning null');
      return null;
    }

    // Cek apakah file adalah PDF menggunakan beberapa metode
    const isPDF = (
      file_detection?.type === 'pdf' ||
      (fileData?.type || '').toLowerCase().trim() === 'pdf' ||
      (fileData?.filename && fileData.filename.toLowerCase().endsWith('.pdf'))
    );

    console.log('isPDF:', isPDF);

    if (!isPDF) {
      console.log('Not a PDF file, returning null');
      return null;
    }

    console.log('Rendering PDF stats component');

    return (
      <div className="space-y-4">
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <h4 className="font-semibold text-red-900 mb-3 flex items-center space-x-2">
            <FileText className="w-5 h-5" />
            <span>Document Statistics</span>
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 text-sm">
            <div className="flex flex-col">
              <span className="text-red-600">Pages:</span> 
              <span className="font-medium text-red-900">
                {analysis_summary.page_count || file_detection?.page_count || 'N/A'}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-red-600">Words:</span> 
              <span className="font-medium text-red-900">
                {analysis_summary.word_count || 'N/A'}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-red-600">Characters:</span> 
              <span className="font-medium text-red-900">
                {analysis_summary.char_count || 'N/A'}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-red-600">Sentences:</span> 
              <span className="font-medium text-red-900">
                {analysis_summary.sentence_count || 'N/A'}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-red-600">Reading Time:</span> 
              <span className="font-medium text-red-900">
                {analysis_summary.reading_time_minutes ? `${analysis_summary.reading_time_minutes} min` : 'N/A'}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-red-600">Avg Words/Page:</span> 
              <span className="font-medium text-red-900">
                {analysis_summary.average_words_per_page || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {analysis_summary.ai_summary && (
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold text-purple-900 mb-3 flex items-center space-x-2">
              <Eye className="w-5 h-5" />
              <span>AI Generated Summary</span>
            </h4>
            <div className="text-purple-800 whitespace-pre-wrap">{analysis_summary.ai_summary}</div>
          </div>
        )}

        {analysis_summary.extraction_info && (
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3">Extraction Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-600">Success Rate:</div>
                <div className="font-medium text-gray-900">
                  {analysis_summary.extraction_info.extraction_success_rate?.toFixed(1) || 'N/A'}%
                </div>
              </div>
              <div>
                <div className="text-gray-600">Pages with Text:</div>
                <div className="font-medium text-gray-900">
                  {analysis_summary.extraction_info.pages_with_text || 'N/A'} /{' '}
                  {analysis_summary.extraction_info.total_pages_processed || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // === Intelligent charts (sesuai backend) ===
  const renderIntelligentCharts = () => {
    const intelligentCharts = analysisData?.intelligent_charts;
    if (!intelligentCharts || Object.keys(intelligentCharts).length === 0) return null;

    const entries = Object.entries(intelligentCharts) as [string, any][];

    const getChartIcon = (type: string) => {
      switch (type) {
        case 'line': return <TrendingUp className="w-4 h-4 text-blue-600" />;
        case 'horizontal_bar': return <BarChart2 className="w-4 h-4 text-green-600" />;
        case 'histogram': return <BarChartIcon className="w-4 h-4 text-purple-600" />;
        case 'scatter': return <Activity className="w-4 h-4 text-orange-600" />;
        case 'pie': return <PieChartIcon className="w-4 h-4 text-pink-600" />;
        case 'area': return <Activity className="w-4 h-4 text-indigo-600" />;
        default: return <BarChartIcon className="w-4 h-4 text-gray-600" />;
      }
    };

    const purposeMap: Record<string, string> = {
      time_series: 'Analisis Tren Waktu',
      ranking: 'Ranking & Perbandingan',
      distribution: 'Distribusi Data',
      correlation: 'Analisis Korelasi',
      proportion: 'Proporsi & Komposisi',
      cumulative: 'Analisis Kumulatif',
    };

    return entries.map(([chartId, chartInfo], idx) => {
      const { type, title, chart_purpose } = chartInfo;

      // LINE / AREA
      if (type === 'line' || type === 'area') {
        const data = (chartInfo.x_data || []).map((x: any, i: number) => ({
          x,
          y: (chartInfo.y_data || [])[i],
        }));

        return (
          <div key={chartId} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                {getChartIcon(type)}
                <div>
                  <span className="font-medium">{title}</span>
                  <div className="text-xs text-gray-500">{purposeMap[chart_purpose] || 'Analisis Data'}</div>
                </div>
              </div>
              {'correlation' in chartInfo && (
                <div className="text-xs text-gray-500">Korelasi: {chartInfo.correlation}</div>
              )}
            </div>

            <ResponsiveContainer width="100%" height={300}>
              {type === 'line' ? (
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="y" stroke="#8884d8" strokeWidth={2} dot={false} />
                </LineChart>
              ) : (
                <AreaChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="x" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="y" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
                </AreaChart>
              )}
            </ResponsiveContainer>
          </div>
        );
      }

      // HORIZONTAL BAR
      if (type === 'horizontal_bar') {
        const data = (chartInfo.y_data || []).map((label: any, i: number) => ({
          label,
          value: (chartInfo.x_data || [])[i],
        }));

        return (
          <div key={chartId} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center space-x-2 mb-4">
              {getChartIcon(type)}
              <div>
                <span className="font-medium">{title}</span>
                <div className="text-xs text-gray-500">{purposeMap[chart_purpose] || 'Analisis Data'}</div>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={Math.max(280, data.length * 28)}>
              <BarChart data={data} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="label" type="category" width={100} />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#82ca9d">
                  {data.map((_d: any, i: number) => (
                    <Cell key={i} fill={chartColors[i % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // HISTOGRAM
      if (type === 'histogram') {
        const data = (chartInfo.bin_centers || []).map((center: number, i: number) => ({
          bin: typeof center === 'number' ? center.toFixed(2) : String(center),
          count: (chartInfo.counts || [])[i],
        }));

        return (
          <div key={chartId} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                {getChartIcon(type)}
                <div>
                  <span className="font-medium">{title}</span>
                  <div className="text-xs text-gray-500">{purposeMap[chart_purpose] || 'Distribusi Data'}</div>
                </div>
              </div>
              {chartInfo.stats && (
                <div className="text-xs text-gray-500">
                  Mean: {chartInfo.stats.mean?.toFixed(2)} | Median: {chartInfo.stats.median?.toFixed(2)}
                </div>
              )}
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8">
                  {data.map((_d: any, i: number) => (
                    <Cell key={i} fill={chartColors[i % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // SCATTER
      if (type === 'scatter') {
        const data = (chartInfo.x_data || []).map((x: any, i: number) => ({
          x,
          y: (chartInfo.y_data || [])[i],
        }));

        return (
          <div key={chartId} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                {getChartIcon(type)}
                <div>
                  <span className="font-medium">{title}</span>
                  <div className="text-xs text-gray-500">{purposeMap[chart_purpose] || 'Analisis Korelasi'}</div>
                </div>
              </div>
              {'correlation' in chartInfo && (
                <div className="text-xs text-gray-500">r = {chartInfo.correlation}</div>
              )}
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" name={chartInfo.x_label || 'x'} />
                <YAxis type="number" dataKey="y" name={chartInfo.y_label || 'y'} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Legend />
                <Scatter name={title} data={data} fill="#ff7c7c" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // PIE
      if (type === 'pie') {
        const data = (chartInfo.labels || []).map((label: any, i: number) => ({
          name: label,
          value: (chartInfo.data || [])[i],
        }));

        return (
          <div key={chartId} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center space-x-2 mb-4">
              {getChartIcon(type)}
              <div>
                <span className="font-medium">{title}</span>
                <div className="text-xs text-gray-500">{purposeMap[chart_purpose] || 'Proporsi & Komposisi'}</div>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Tooltip />
                <Legend />
                <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
                  {data.map((_entry: any, i: number) => (
                    <Cell key={i} fill={chartColors[i % chartColors.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        );
      }

      return null;
    });
  };

  // === Legacy charts (analysis_summary.charts) ===
  const renderLegacyCharts = () => {
    const charts = analysisData?.charts;
    if (!charts || Object.keys(charts).length === 0) return null;

    return Object.entries(charts).map(([colName, cfg]: [string, any], idx) => {
      if (cfg.type === 'histogram') {
        const data =
          (cfg.bins || []).slice(0, -1).map((start: number, i: number) => {
            const end = cfg.bins[i + 1];
            const center = (Number(start) + Number(end)) / 2;
            return {
              bin: typeof center === 'number' ? center.toFixed(2) : String(center),
              count: (cfg.counts || [])[i],
            };
          }) || [];

        return (
          <div key={idx} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center space-x-2 mb-4">
              <BarChartIcon className="w-4 h-4 text-purple-600" />
              <div>
                <span className="font-medium">Distribusi {colName}</span>
                {cfg.stats && (
                  <div className="text-xs text-gray-500">
                    Mean: {cfg.stats.mean?.toFixed(2)} | Median: {cfg.stats.median?.toFixed(2)}
                  </div>
                )}
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      if (cfg.type === 'bar') {
        const data = (cfg.categories || []).map((cat: string, i: number) => ({
          label: cat,
          value: (cfg.counts || [])[i],
        }));

        return (
          <div key={idx} className="bg-white border rounded-lg p-4 shadow-sm">
            <div className="flex items-center space-x-2 mb-4">
              <BarChart2 className="w-4 h-4 text-green-600" />
              <div>
                <span className="font-medium">Distribusi {colName}</span>
                <div className="text-xs text-gray-500">
                  Unique: {cfg.total_unique} | Top%: {cfg.top_category_percentage}%
                </div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={Math.max(280, data.length * 28)}>
              <BarChart data={data} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="label" width={120} />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#82ca9d">
                  {data.map((_d: any, i: number) => (
                    <Cell key={i} fill={chartColors[i % chartColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      return null;
    });
  };

  // === Excel note (opsional ringkas) ===
  const renderExcelHeader = () => {
    if (fileData?.type !== 'excel' && file_detection?.type !== 'excel') return null;
    
    // Try to get info from analysis_summary first, then from file_detection
    const totalSheets = analysis_summary?.total_sheets || file_detection?.sheet_count || 1;
    const totalRows = analysis_summary?.total_rows || 'N/A';
    const totalCols = analysis_summary?.total_columns || 'N/A';
    
    return (
      <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-200">
        <h4 className="font-semibold text-emerald-900 mb-2 flex items-center space-x-2">
          <FileSpreadsheet className="w-5 h-5" />
          <span>Excel Overview</span>
        </h4>
        <div className="text-sm text-emerald-900">
          Sheets: <b>{totalSheets}</b> • Rows: <b>{totalRows}</b> • Columns: <b>{totalCols}</b>
        </div>
      </div>
    );
  };

  // === Empty state ===
  const renderEmpty = () => (
    <div className="text-sm text-gray-500 px-2">Tidak ada visualisasi yang dapat ditampilkan.</div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{fileData?.filename}</h3>
          <p className="text-xs text-gray-500">File ID: {fileData?.file_id}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Target className="w-4 h-4" />
          <span>{(fileData?.type || '').toUpperCase()}</span>
        </div>
      </div>

      {/* File detection */}
      {renderFileDetection()}

      {/* Excel overview (ringkas) */}
      {renderExcelHeader()}

      {/* PDF stats */}
      {renderPDFStats()}

      {/* Column types + Data quality */}
      {renderColumnTypes()}
      {renderDataQuality()}

      {/* Intelligent charts (utama dari backend terbaru) */}
      {renderIntelligentCharts() || renderLegacyCharts() || renderEmpty()}
    </div>
  );
};

export default DataVisualization;