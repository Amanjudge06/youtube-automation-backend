import React, { useState, useEffect } from 'react';
import { FileText, Download, RefreshCw, AlertCircle, Info, CheckCircle, XCircle } from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchLogs();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchLogs, 3000); // Refresh every 3 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/logs');
      const data = await response.json();
      setLogs(data.logs.filter(log => log.trim())); // Remove empty lines
    } catch (error) {
      console.error('Error fetching logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadLogs = () => {
    const logContent = logs.join('\n');
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `automation-logs-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearLogs = () => {
    if (window.confirm('Are you sure you want to clear the current log view?')) {
      setLogs([]);
    }
  };

  const parseLogLevel = (logLine) => {
    if (logLine.includes('ERROR')) return 'error';
    if (logLine.includes('WARNING') || logLine.includes('WARN')) return 'warning';
    if (logLine.includes('INFO')) return 'info';
    if (logLine.includes('SUCCESS') || logLine.includes('✅')) return 'success';
    return 'debug';
  };

  const formatLogTime = (logLine) => {
    const timeMatch = logLine.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/);
    return timeMatch ? timeMatch[1] : '';
  };

  const formatLogMessage = (logLine) => {
    // Remove timestamp and level info to get clean message
    return logLine.replace(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - .+ - \w+ - /, '');
  };

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    return parseLogLevel(log) === filter;
  });

  const LogLine = ({ log, index }) => {
    const level = parseLogLevel(log);
    const time = formatLogTime(log);
    const message = formatLogMessage(log);
    
    const levelConfig = {
      error: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
      warning: { icon: AlertCircle, color: 'text-yellow-600', bg: 'bg-yellow-50' },
      success: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
      info: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50' },
      debug: { icon: FileText, color: 'text-gray-600', bg: 'bg-gray-50' }
    };
    
    const config = levelConfig[level] || levelConfig.debug;
    const Icon = config.icon;
    
    return (
      <div className={`p-3 border-l-4 ${config.bg} border-l-${level === 'error' ? 'red' : level === 'warning' ? 'yellow' : level === 'success' ? 'green' : level === 'info' ? 'blue' : 'gray'}-400`}>
        <div className="flex items-start space-x-2">
          <Icon className={`w-4 h-4 mt-0.5 ${config.color} flex-shrink-0`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500 font-mono">
                {time || `Line ${index + 1}`}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded ${config.color} ${config.bg} border`}>
                {level.toUpperCase()}
              </span>
            </div>
            <p className="text-sm text-gray-900 mt-1 font-mono break-words">
              {message || log}
            </p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Logs</h1>
          <p className="text-gray-600">Monitor automation activity and system events</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span>Auto Refresh</span>
          </label>
          
          <button
            onClick={downloadLogs}
            disabled={logs.length === 0}
            className="flex items-center px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 text-sm"
          >
            <Download className="w-4 h-4 mr-1" />
            Export
          </button>
          
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats and Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-4 sm:space-y-0">
            {/* Log Stats */}
            <div className="flex items-center space-x-6">
              <div className="text-sm">
                <span className="text-gray-500">Total:</span>
                <span className="ml-1 font-medium">{logs.length}</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-500">Errors:</span>
                <span className="ml-1 font-medium text-red-600">
                  {logs.filter(log => parseLogLevel(log) === 'error').length}
                </span>
              </div>
              <div className="text-sm">
                <span className="text-gray-500">Warnings:</span>
                <span className="ml-1 font-medium text-yellow-600">
                  {logs.filter(log => parseLogLevel(log) === 'warning').length}
                </span>
              </div>
            </div>
            
            {/* Filter */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Filter:</span>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="all">All Logs</option>
                <option value="error">Errors Only</option>
                <option value="warning">Warnings Only</option>
                <option value="success">Success Only</option>
                <option value="info">Info Only</option>
                <option value="debug">Debug Only</option>
              </select>
            </div>
          </div>
        </div>
        
        {/* Auto Refresh Indicator */}
        {autoRefresh && (
          <div className="px-4 py-2 bg-blue-50 border-b border-gray-200">
            <div className="flex items-center text-sm text-blue-700">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
              Auto-refreshing every 3 seconds
            </div>
          </div>
        )}
      </div>

      {/* Logs Display */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">Log Entries</h3>
            {logs.length > 0 && (
              <button
                onClick={clearLogs}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Clear View
              </button>
            )}
          </div>
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {filteredLogs.length > 0 ? (
            <div className="space-y-1 p-1">
              {filteredLogs.map((log, index) => (
                <LogLine key={index} log={log} index={index} />
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No logs available</h3>
              <p className="mt-1 text-sm text-gray-500">
                {loading ? 'Loading logs...' : 'Run the automation to generate logs.'}
              </p>
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No logs match filter</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try changing the filter or clearing it to see all logs.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Log Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <Info className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Log Tips</h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc pl-5 space-y-1">
                <li>Logs automatically refresh when auto-refresh is enabled</li>
                <li>Use filters to focus on specific log levels (errors, warnings, etc.)</li>
                <li>Export logs to file for detailed analysis or sharing</li>
                <li>Error logs are highlighted in red for quick identification</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Logs;