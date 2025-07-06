import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useProjectDataImproved } from '../useProjectDataImproved';
import { ProjectData } from '../../types';

// Mock the toast hook
vi.mock('../use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock fetch globally
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  configurable: true,
  value: true
});

describe('useProjectDataImproved', () => {
  const mockProjectData: ProjectData = {
    summary: {
      title: 'Test Project',
      description: 'Test Description',
      domain: 'test',
      repository: 'test/repo',
      branch: 'main'
    },
    phases: [
      {
        id: 'phase1',
        title: 'Phase 1',
        description: 'First phase',
        roles: ['Developer'],
        issues: [],
        approved: false
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (global.fetch as any).mockReset();
    navigator.onLine = true;
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('initial fetch', () => {
    it('should fetch project data on mount', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectData
      });

      const { result } = renderHook(() => useProjectDataImproved());

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.projectData).toEqual(mockProjectData);
      expect(result.current.error).toBe(null);
      expect(result.current.lastFetchTime).toBeInstanceOf(Date);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/project',
        expect.objectContaining({
          signal: expect.any(AbortSignal),
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    it('should cache successful response', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectData
      });

      renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'project-data-cache',
          JSON.stringify(mockProjectData)
        );
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'project-data-cache-time',
        expect.any(String)
      );
    });

    it('should use custom API URL', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectData
      });

      renderHook(() => useProjectDataImproved({ apiUrl: 'https://custom-api.com' }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'https://custom-api.com/api/project',
          expect.any(Object)
        );
      });
    });
  });

  describe('error handling', () => {
    it('should handle 404 errors with specific message', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.error).toBe('Project data not found. Please run the CLI tool first.');
      });
    });

    it('should handle server errors (5xx)', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.error).toBe('Server error. Please try again later.');
      });
    });

    it('should handle other HTTP errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to fetch project data (403)');
      });
    });

    it('should validate response data format', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ invalid: 'data' })
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.error).toBe('Invalid project data format');
      });
    });

    it('should handle network errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });
    });

    it('should handle abort errors silently', async () => {
      const abortError = new Error('Aborted');
      abortError.name = 'AbortError';
      (global.fetch as any).mockRejectedValueOnce(abortError);

      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {});

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(consoleLog).toHaveBeenCalledWith('Request aborted');
      expect(result.current.error).toBe(null);

      consoleLog.mockRestore();
    });
  });

  describe('retry logic', () => {
    it('should retry with exponential backoff', async () => {
      (global.fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        });

      const { result } = renderHook(() => useProjectDataImproved({
        maxRetries: 3,
        retryDelay: 100
      }));

      // First attempt fails
      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      // First retry after 100ms
      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });

      // Second retry after 200ms (exponential backoff)
      act(() => {
        vi.advanceTimersByTime(200);
      });

      await waitFor(() => {
        expect(result.current.projectData).toEqual(mockProjectData);
      });

      expect(global.fetch).toHaveBeenCalledTimes(3);
    });

    it('should stop retrying after max retries', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Persistent error'));

      const { result } = renderHook(() => useProjectDataImproved({
        maxRetries: 2,
        retryDelay: 50
      }));

      await waitFor(() => {
        expect(result.current.error).toBe('Persistent error');
      });

      // Wait for all retries
      act(() => {
        vi.advanceTimersByTime(150); // 50ms + 100ms
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
      });

      // No more retries after max
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(global.fetch).toHaveBeenCalledTimes(3);
    });

    it('should reset retry count on successful fetch', async () => {
      (global.fetch as any)
        .mockRejectedValueOnce(new Error('Temporary error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        });

      const { result } = renderHook(() => useProjectDataImproved({
        retryDelay: 100
      }));

      await waitFor(() => {
        expect(result.current.error).toBe('Temporary error');
      });

      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(result.current.projectData).toEqual(mockProjectData);
      });

      // Refetch should start fresh with retry count
      (global.fetch as any)
        .mockRejectedValueOnce(new Error('Another error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        });

      await act(async () => {
        await result.current.refetch();
      });

      // Should retry with initial delay (not exponential)
      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(5);
      });
    });
  });

  describe('offline support', () => {
    it('should load from cache when offline', async () => {
      navigator.onLine = false;
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'project-data-cache') return JSON.stringify(mockProjectData);
        if (key === 'project-data-cache-time') return '2024-01-01T00:00:00Z';
        return null;
      });

      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.projectData).toEqual(mockProjectData);
      });

      expect(result.current.error).toBe('Network error');
    });

    it('should handle online/offline events', async () => {
      const { result } = renderHook(() => useProjectDataImproved());

      expect(result.current.isOnline).toBe(true);

      // Go offline
      act(() => {
        navigator.onLine = false;
        window.dispatchEvent(new Event('offline'));
      });

      expect(result.current.isOnline).toBe(false);

      // Go online
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectData
      });

      act(() => {
        navigator.onLine = true;
        window.dispatchEvent(new Event('online'));
      });

      expect(result.current.isOnline).toBe(true);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2); // Initial + refetch on online
      });
    });

    it('should cleanup event listeners on unmount', () => {
      const removeEventListener = vi.spyOn(window, 'removeEventListener');

      const { unmount } = renderHook(() => useProjectDataImproved());

      unmount();

      expect(removeEventListener).toHaveBeenCalledWith('online', expect.any(Function));
      expect(removeEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
    });
  });

  describe('updateProjectData', () => {
    it('should update data optimistically', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.projectData).toEqual(mockProjectData);
      });

      const updatedData = {
        ...mockProjectData,
        summary: { ...mockProjectData.summary, title: 'Updated' }
      };

      await act(async () => {
        await result.current.updateProjectData(updatedData);
      });

      expect(result.current.projectData).toEqual(updatedData);
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'project-data-cache',
        JSON.stringify(updatedData)
      );
    });

    it('should rollback on update error', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: false
        });

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.projectData).toEqual(mockProjectData);
      });

      const updatedData = {
        ...mockProjectData,
        summary: { ...mockProjectData.summary, title: 'Updated' }
      };

      await expect(
        result.current.updateProjectData(updatedData)
      ).rejects.toThrow();

      // Should rollback to original data
      expect(result.current.projectData).toEqual(mockProjectData);
    });

    it('should store pending updates when offline', async () => {
      navigator.onLine = false;

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(result.current.projectData).toEqual(mockProjectData);
      });

      localStorageMock.getItem.mockReturnValue('[]');

      const updatedData = {
        ...mockProjectData,
        summary: { ...mockProjectData.summary, title: 'Updated' }
      };

      await expect(
        result.current.updateProjectData(updatedData)
      ).rejects.toThrow();

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'pending-updates',
        expect.stringContaining('"type":"update"')
      );
    });
  });

  describe('createGitHubIssues', () => {
    it('should create issues successfully', async () => {
      const mockResult = { epicsCreated: 3, issuesCreated: 10 };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult
      });

      const { result } = renderHook(() => useProjectDataImproved());

      const phases = mockProjectData.phases;
      const response = await result.current.createGitHubIssues(phases);

      expect(response).toEqual(mockResult);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/github/create-issues',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phases })
        })
      );
    });

    it('should handle authentication errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ details: 'Unauthorized' })
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('GitHub authentication required. Please check your token.');
    });

    it('should handle rate limit errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ details: 'Rate limited' })
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('GitHub API rate limit exceeded. Please try again later.');
    });

    it('should handle generic errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ details: 'Server error' })
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('Server error');
    });

    it('should handle malformed error responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => { throw new Error('Invalid JSON'); }
      });

      const { result } = renderHook(() => useProjectDataImproved());

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('Unknown error');
    });
  });

  describe('abort and cleanup', () => {
    it('should abort pending requests on unmount', async () => {
      let abortSignal: AbortSignal | null = null;

      (global.fetch as any).mockImplementation(async (url: string, options: any) => {
        abortSignal = options.signal;
        return new Promise(() => {}); // Never resolves
      });

      const { unmount } = renderHook(() => useProjectDataImproved());

      await waitFor(() => {
        expect(abortSignal).not.toBeNull();
      });

      unmount();

      expect(abortSignal?.aborted).toBe(true);
    });

    it('should cancel retry timeout on unmount', async () => {
      (global.fetch as any).mockRejectedValue(new Error('Network error'));

      const { unmount } = renderHook(() => useProjectDataImproved({
        retryDelay: 5000
      }));

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });

      unmount();

      // Advance time to when retry would occur
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // Should not have retried after unmount
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('retry method', () => {
    it('should force retry and clear pending timeouts', async () => {
      (global.fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        });

      const { result } = renderHook(() => useProjectDataImproved({
        retryDelay: 5000
      }));

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      // Manually retry before automatic retry
      await act(async () => {
        await result.current.retry();
      });

      expect(result.current.projectData).toEqual(mockProjectData);
      expect(global.fetch).toHaveBeenCalledTimes(2);

      // Advance time to when automatic retry would have occurred
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // Should not have called fetch again
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });
});