import React, { useState, useEffect } from 'react';
import LogViewer from './LogViewer';
import './App.css';

function App() {
  const [taskInfo, setTaskInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [taskComplete, setTaskComplete] = useState(false);

  // Get task ID from URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const taskId = urlParams.get('taskId');

  useEffect(() => {
    // Fetch initial task information
    const fetchTaskInfo = async () => {
      if (!taskId) {
        setError('No task ID provided in URL');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/status?task_id=${taskId}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch task info: ${response.status}`);
        }
        
        const data = await response.json();
        setTaskInfo(data);
        setIsLoading(false);
      } catch (err) {
        setError(err.message);
        setIsLoading(false);
      }
    };

    fetchTaskInfo();
  }, [taskId]);

  const handleTaskComplete = (finalStatus) => {
    setTaskComplete(true);
    setTaskInfo(finalStatus);
  };

  if (isLoading) {
    return (
      <div className="app loading">
        <div className="spinner"></div>
        <p>Loading task information...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app error">
        <h1>Error</h1>
        <p>{error}</p>
        <a href="/">Back to Home</a>
      </div>
    );
  }

  if (!taskInfo) {
    return (
      <div className="app error">
        <h1>Task Not Found</h1>
        <p>The requested task could not be found.</p>
        <a href="/">Back to Home</a>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>GitHub Backlog Generator</h1>
        <div className="task-info">
          <span>Repository: {taskInfo.repository || 'Unknown'}</span>
          <span>Phase: {taskInfo.phase || 'All'}</span>
          {taskInfo.duration && <span>Duration: {Math.round(taskInfo.duration / 60)}m</span>}
        </div>
      </header>
      
      <main className="app-main">
        <LogViewer
          apiUrl="/api"
          taskId={taskId}
          logStream={taskInfo.logStream}
          onComplete={handleTaskComplete}
        />
      </main>
      
      {taskComplete && (
        <div className="completion-banner">
          <h2>✓ Task Completed Successfully!</h2>
          <p>The GitHub backlog generation has finished. Check your repository for the created issues.</p>
          <button onClick={() => window.location.href = taskInfo.repositoryUrl}>
            View Repository
          </button>
        </div>
      )}
    </div>
  );
}

export default App;