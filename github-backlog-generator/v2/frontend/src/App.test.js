import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock LogViewer component
jest.mock('./LogViewer', () => {
  return function LogViewer({ onComplete }) {
    return (
      <div data-testid="log-viewer">
        <button onClick={() => onComplete({ lastStatus: 'STOPPED' })}>
          Complete Task
        </button>
      </div>
    );
  };
});

// Mock fetch
global.fetch = jest.fn();

describe('App Component', () => {
  const mockTaskInfo = {
    taskId: 'task-12345',
    repository: 'owner/repo',
    phase: 'planning',
    logStream: 'ecs/logs/stream',
    lastStatus: 'RUNNING',
    repositoryUrl: 'https://github.com/owner/repo'
  };

  beforeEach(() => {
    fetch.mockClear();
    // Reset URL
    window.history.pushState({}, '', '/');
  });

  test('shows error when no task ID in URL', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('No task ID provided in URL')).toBeInTheDocument();
    });
  });

  test('shows loading state initially', () => {
    window.history.pushState({}, '', '/?taskId=task-12345');
    render(<App />);
    
    expect(screen.getByText('Loading task information...')).toBeInTheDocument();
  });

  test('fetches and displays task information', async () => {
    window.history.pushState({}, '', '/?taskId=task-12345');
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTaskInfo
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('GitHub Backlog Generator')).toBeInTheDocument();
      expect(screen.getByText('Repository: owner/repo')).toBeInTheDocument();
      expect(screen.getByText('Phase: planning')).toBeInTheDocument();
    });
    
    expect(fetch).toHaveBeenCalledWith('/api/status?task_id=task-12345');
  });

  test('shows error when fetch fails', async () => {
    window.history.pushState({}, '', '/?taskId=task-12345');
    
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  test('shows task not found when response is not ok', async () => {
    window.history.pushState({}, '', '/?taskId=task-12345');
    
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 404
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch task info/)).toBeInTheDocument();
    });
  });

  test('shows completion banner when task completes', async () => {
    window.history.pushState({}, '', '/?taskId=task-12345');
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTaskInfo
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByTestId('log-viewer')).toBeInTheDocument();
    });
    
    // Simulate task completion
    const completeButton = screen.getByText('Complete Task');
    completeButton.click();
    
    await waitFor(() => {
      expect(screen.getByText('✓ Task Completed Successfully!')).toBeInTheDocument();
      expect(screen.getByText('View Repository')).toBeInTheDocument();
    });
  });

  test('displays duration when available', async () => {
    window.history.pushState({}, '', '/?taskId=task-12345');
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        ...mockTaskInfo,
        duration: 1800 // 30 minutes in seconds
      })
    });
    
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Duration: 30m')).toBeInTheDocument();
    });
  });
});