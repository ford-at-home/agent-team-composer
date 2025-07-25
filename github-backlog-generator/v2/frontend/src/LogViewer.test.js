import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LogViewer from './LogViewer';

// Mock fetch
global.fetch = jest.fn();

describe('LogViewer Component', () => {
  const defaultProps = {
    apiUrl: 'https://api.example.com',
    taskId: 'task-12345678',
    logStream: 'ecs/github-backlog-generator/abc123',
    onComplete: jest.fn(),
  };

  beforeEach(() => {
    fetch.mockClear();
    defaultProps.onComplete.mockClear();
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  test('renders with initial loading state', () => {
    render(<LogViewer {...defaultProps} />);
    
    expect(screen.getByText(/Task Logs: task-12345678/)).toBeInTheDocument();
    expect(screen.getByText(/Waiting for logs.../)).toBeInTheDocument();
  });

  test('fetches and displays logs', async () => {
    const mockLogs = {
      events: [
        {
          timestamp: '2024-01-15T10:00:00.000Z',
          message: 'Starting GitHub Backlog Generator...',
          eventId: '1'
        },
        {
          timestamp: '2024-01-15T10:00:01.000Z',
          message: 'Fetching repository information',
          eventId: '2'
        }
      ],
      nextToken: 'token123',
      hasMore: true
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockLogs
    });

    render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Starting GitHub Backlog Generator...')).toBeInTheDocument();
      expect(screen.getByText('Fetching repository information')).toBeInTheDocument();
    });

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/logs?log_stream=ecs/github-backlog-generator/abc123'),
      expect.any(Object)
    );
  });

  test('handles log filtering', async () => {
    const mockLogs = {
      events: [
        {
          timestamp: '2024-01-15T10:00:00.000Z',
          message: 'Starting task',
          eventId: '1'
        },
        {
          timestamp: '2024-01-15T10:00:01.000Z',
          message: 'Processing repository',
          eventId: '2'
        },
        {
          timestamp: '2024-01-15T10:00:02.000Z',
          message: 'Task completed',
          eventId: '3'
        }
      ],
      hasMore: false
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockLogs
    });

    render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Starting task')).toBeInTheDocument();
    });

    // Apply filter
    const filterInput = screen.getByPlaceholderText('Filter logs...');
    fireEvent.change(filterInput, { target: { value: 'repository' } });

    // Only matching log should be visible
    expect(screen.queryByText('Starting task')).not.toBeInTheDocument();
    expect(screen.getByText('Processing repository')).toBeInTheDocument();
    expect(screen.queryByText('Task completed')).not.toBeInTheDocument();
  });

  test('copy logs to clipboard', async () => {
    const mockLogs = {
      events: [
        {
          timestamp: '2024-01-15T10:00:00.000Z',
          message: 'Test log entry',
          eventId: '1'
        }
      ],
      hasMore: false
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockLogs
    });

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue()
      }
    });

    render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test log entry')).toBeInTheDocument();
    });

    const copyButton = screen.getByText('Copy');
    fireEvent.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('Test log entry')
    );
  });

  test('download logs as file', async () => {
    const mockLogs = {
      events: [
        {
          timestamp: '2024-01-15T10:00:00.000Z',
          message: 'Test log for download',
          eventId: '1'
        }
      ],
      hasMore: false
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockLogs
    });

    // Mock URL.createObjectURL
    global.URL.createObjectURL = jest.fn(() => 'blob:test');
    global.URL.revokeObjectURL = jest.fn();

    // Mock createElement and click
    const mockAnchor = { 
      href: '', 
      download: '', 
      click: jest.fn() 
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor);
    jest.spyOn(document.body, 'appendChild').mockImplementation();
    jest.spyOn(document.body, 'removeChild').mockImplementation();

    render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test log for download')).toBeInTheDocument();
    });

    const downloadButton = screen.getByText('Download');
    fireEvent.click(downloadButton);

    expect(mockAnchor.download).toContain('github-backlog-task-12345678');
    expect(mockAnchor.click).toHaveBeenCalled();
  });

  test('handles API errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Connection error/)).toBeInTheDocument();
    });
  });

  test('stops streaming when task completes', async () => {
    const mockLogs = {
      events: [],
      hasMore: false
    };

    const mockStatus = {
      lastStatus: 'STOPPED',
      taskId: 'task-12345678',
      duration: 1800
    };

    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockLogs
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      });

    render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('✓ Complete')).toBeInTheDocument();
    });

    expect(defaultProps.onComplete).toHaveBeenCalledWith(mockStatus);
  });

  test('auto-scroll behavior', async () => {
    const mockLogs = {
      events: Array.from({ length: 50 }, (_, i) => ({
        timestamp: `2024-01-15T10:00:${String(i).padStart(2, '0')}.000Z`,
        message: `Log entry ${i + 1}`,
        eventId: String(i + 1)
      })),
      hasMore: false
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockLogs
    });

    const { container } = render(<LogViewer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText('Log entry 1')).toBeInTheDocument();
    });

    const logContainer = container.querySelector('.log-container');
    
    // Should show auto-scrolling indicator
    expect(screen.getByText('↓ Auto-scrolling')).toBeInTheDocument();

    // Simulate user scrolling up
    fireEvent.scroll(logContainer, { target: { scrollTop: 0 } });

    // Should show scroll paused indicator
    expect(screen.getByText('⏸ Scroll paused')).toBeInTheDocument();
  });
});