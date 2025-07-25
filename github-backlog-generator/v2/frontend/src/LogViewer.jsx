import React, { useState, useEffect, useRef, useCallback } from 'react';
import './LogViewer.css';

/**
 * LogViewer Component
 * 
 * Real-time log streaming component for GitHub Backlog Generator tasks.
 * 
 * Props:
 * - apiUrl: Base URL for the API (required)
 * - taskId: The task ID to stream logs for (required)
 * - logStream: The CloudWatch log stream name (required)
 * - onComplete: Callback when task completes (optional)
 * - pollInterval: Polling interval in ms (default: 2000)
 * - maxRetries: Max retries for failed requests (default: 3)
 */
const LogViewer = ({ 
  apiUrl, 
  taskId, 
  logStream, 
  onComplete,
  pollInterval = 2000,
  maxRetries = 3
}) => {
  const [logs, setLogs] = useState([]);
  const [nextToken, setNextToken] = useState(null);
  const [isStreaming, setIsStreaming] = useState(true);
  const [error, setError] = useState(null);
  const [taskStatus, setTaskStatus] = useState('RUNNING');
  const [retryCount, setRetryCount] = useState(0);
  
  const logContainerRef = useRef(null);
  const intervalRef = useRef(null);
  const isAutoScrolling = useRef(true);

  // Fetch logs from API
  const fetchLogs = useCallback(async () => {
    if (!isStreaming || !logStream) return;

    try {
      const params = new URLSearchParams({
        log_stream: logStream,
        ...(nextToken && { next_token: nextToken })
      });

      const response = await fetch(`${apiUrl}/logs?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Reset retry count on successful fetch
      setRetryCount(0);
      setError(null);

      // Append new logs
      if (data.events && data.events.length > 0) {
        setLogs(prevLogs => [...prevLogs, ...data.events]);
      }

      // Update next token for pagination
      if (data.nextToken !== nextToken) {
        setNextToken(data.nextToken);
      }

      // Check if we should continue streaming
      if (!data.hasMore && data.events.length === 0) {
        // No more logs, check task status
        checkTaskStatus();
      }

    } catch (err) {
      console.error('Error fetching logs:', err);
      
      // Retry logic
      if (retryCount < maxRetries) {
        setRetryCount(prev => prev + 1);
        setError(`Connection error. Retrying... (${retryCount + 1}/${maxRetries})`);
      } else {
        setError('Failed to fetch logs. Please check your connection.');
        setIsStreaming(false);
      }
    }
  }, [apiUrl, logStream, nextToken, isStreaming, retryCount, maxRetries]);

  // Check task status
  const checkTaskStatus = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/status?task_id=${taskId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTaskStatus(data.lastStatus);

      // Stop streaming if task is no longer running
      if (data.lastStatus !== 'RUNNING' && data.lastStatus !== 'PROVISIONING') {
        setIsStreaming(false);
        if (onComplete) {
          onComplete(data);
        }
      }

    } catch (err) {
      console.error('Error checking task status:', err);
    }
  }, [apiUrl, taskId, onComplete]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (isAutoScrolling.current && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Handle user scroll
  const handleScroll = useCallback(() => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
      // Check if user is near the bottom (within 50px)
      isAutoScrolling.current = scrollHeight - scrollTop - clientHeight < 50;
    }
  }, []);

  // Start polling for logs
  useEffect(() => {
    fetchLogs(); // Initial fetch

    // Set up polling interval
    intervalRef.current = setInterval(fetchLogs, pollInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchLogs, pollInterval]);

  // Copy logs to clipboard
  const copyToClipboard = useCallback(() => {
    const logText = logs.map(log => `${log.timestamp} ${log.message}`).join('\n');
    navigator.clipboard.writeText(logText).then(() => {
      // Show temporary success message
      const button = document.querySelector('.copy-button');
      if (button) {
        button.textContent = '✓ Copied!';
        setTimeout(() => {
          button.textContent = 'Copy';
        }, 2000);
      }
    });
  }, [logs]);

  // Download logs as file
  const downloadLogs = useCallback(() => {
    const logText = logs.map(log => `${log.timestamp} ${log.message}`).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `github-backlog-${taskId}-${new Date().toISOString()}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [logs, taskId]);

  // Filter logs
  const [filter, setFilter] = useState('');
  const filteredLogs = logs.filter(log => 
    !filter || log.message.toLowerCase().includes(filter.toLowerCase())
  );

  // Render status indicator
  const renderStatus = () => {
    if (error) {
      return <span className="status error">⚠️ {error}</span>;
    }
    
    switch (taskStatus) {
      case 'PROVISIONING':
        return <span className="status provisioning">🔄 Starting...</span>;
      case 'RUNNING':
        return <span className="status streaming">● Streaming</span>;
      case 'STOPPED':
        return <span className="status complete">✓ Complete</span>;
      case 'FAILED':
        return <span className="status failed">✗ Failed</span>;
      default:
        return <span className="status">{taskStatus}</span>;
    }
  };

  return (
    <div className="log-viewer">
      <div className="log-header">
        <div className="log-title">
          <h3>Task Logs: {taskId}</h3>
          {renderStatus()}
        </div>
        <div className="log-controls">
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="filter-input"
          />
          <button onClick={copyToClipboard} className="copy-button" title="Copy logs">
            Copy
          </button>
          <button onClick={downloadLogs} className="download-button" title="Download logs">
            Download
          </button>
        </div>
      </div>
      
      <div 
        className="log-container" 
        ref={logContainerRef}
        onScroll={handleScroll}
      >
        {filteredLogs.length === 0 ? (
          <div className="log-empty">
            {isStreaming ? 'Waiting for logs...' : 'No logs to display'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={`${log.eventId || index}`} className="log-entry">
              <span className="timestamp">{formatTimestamp(log.timestamp)}</span>
              <span className="message">{highlightFilter(log.message, filter)}</span>
            </div>
          ))
        )}
      </div>
      
      <div className="log-footer">
        <div className="log-stats">
          {logs.length} entries {filter && `(${filteredLogs.length} shown)`}
        </div>
        <div className="auto-scroll-indicator">
          {isAutoScrolling.current ? '↓ Auto-scrolling' : '⏸ Scroll paused'}
        </div>
      </div>
    </div>
  );
};

// Helper function to format timestamp
const formatTimestamp = (timestamp) => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  } catch {
    return timestamp;
  }
};

// Helper function to highlight filter matches
const highlightFilter = (text, filter) => {
  if (!filter) return text;
  
  const parts = text.split(new RegExp(`(${filter})`, 'gi'));
  return parts.map((part, index) => 
    part.toLowerCase() === filter.toLowerCase() ? 
      <mark key={index}>{part}</mark> : part
  );
};

export default LogViewer;