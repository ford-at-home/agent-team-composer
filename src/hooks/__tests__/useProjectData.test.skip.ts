import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useProjectData } from '../useProjectData';
import { ProjectData } from '../../types';

// Mock the toast hook
vi.mock('../use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock fetch globally
global.fetch = vi.fn();

describe('useProjectData', () => {
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
    (global.fetch as any).mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('should start with loading state', () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectData
      });

      const { result } = renderHook(() => useProjectData());

      expect(result.current.loading).toBe(true);
      expect(result.current.projectData).toBe(null);
      expect(result.current.error).toBe(null);
    });
  });

  describe('fetchProjectData', () => {
    it('should fetch project data on mount', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjectData
      });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.projectData).toEqual(mockProjectData);
      expect(result.current.error).toBe(null);
      expect(global.fetch).toHaveBeenCalledWith('http://localhost:3000/api/project');
    });

    it('should handle fetch errors', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false
      });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to fetch project data');
      expect(result.current.projectData).toBe(null);

      // Check if toast was called
      const { useToast } = await import('../use-toast');
      const toastMock = vi.mocked(useToast().toast);
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Error loading project data',
        description: 'Please ensure the CLI tool is running',
        variant: 'destructive'
      });
    });

    it('should handle network errors', async () => {
      const networkError = new Error('Network error');
      (global.fetch as any).mockRejectedValueOnce(networkError);

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network error');
      expect(result.current.projectData).toBe(null);
    });

    it('should handle non-Error exceptions', async () => {
      (global.fetch as any).mockRejectedValueOnce('String error');

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Unknown error');
    });

    it('should refetch data when refetch is called', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockProjectData, summary: { ...mockProjectData.summary, title: 'Updated' } })
        });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.projectData?.summary.title).toBe('Test Project');

      // Call refetch
      result.current.refetch();

      await waitFor(() => {
        expect(result.current.projectData?.summary.title).toBe('Updated');
      });

      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('updateProjectData', () => {
    it('should update project data successfully', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: true
        });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const updatedData: ProjectData = {
        ...mockProjectData,
        summary: { ...mockProjectData.summary, title: 'Updated Title' }
      };

      await result.current.updateProjectData(updatedData);

      expect(result.current.projectData).toEqual(updatedData);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/project',
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updatedData)
        }
      );
    });

    it('should handle update errors', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: false
        });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        result.current.updateProjectData(mockProjectData)
      ).rejects.toThrow('Failed to update project data');

      // Project data should remain unchanged
      expect(result.current.projectData).toEqual(mockProjectData);

      // Check if toast was called
      const { useToast } = await import('../use-toast');
      const toastMock = vi.mocked(useToast().toast);
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Error updating project data',
        description: 'Failed to update project data',
        variant: 'destructive'
      });
    });

    it('should handle network errors during update', async () => {
      const error = new Error('Network failed');
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockRejectedValueOnce(error);

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        result.current.updateProjectData(mockProjectData)
      ).rejects.toThrow('Network failed');
    });
  });

  describe('createGitHubIssues', () => {
    it('should create GitHub issues successfully', async () => {
      const mockResult = { created: 5, issues: [] };
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResult
        });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const issueResult = await result.current.createGitHubIssues(mockProjectData.phases);

      expect(issueResult).toEqual(mockResult);
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:3000/api/github/create-issues',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phases: mockProjectData.phases })
        }
      );
    });

    it('should handle GitHub API errors with details', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: false,
          json: async () => ({ details: 'Rate limit exceeded' })
        });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('Rate limit exceeded');

      // Check if toast was called
      const { useToast } = await import('../use-toast');
      const toastMock = vi.mocked(useToast().toast);
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Error creating GitHub issues',
        description: 'Rate limit exceeded',
        variant: 'destructive'
      });
    });

    it('should handle GitHub API errors without details', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockResolvedValueOnce({
          ok: false,
          json: async () => ({})
        });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('Failed to create GitHub issues');
    });

    it('should handle network errors during issue creation', async () => {
      const error = new Error('Connection failed');
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockRejectedValueOnce(error);

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('Connection failed');
    });

    it('should handle non-Error exceptions during issue creation', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockProjectData
        })
        .mockRejectedValueOnce('String error');

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(
        result.current.createGitHubIssues(mockProjectData.phases)
      ).rejects.toThrow('Unknown error');

      // Check if toast was called
      const { useToast } = await import('../use-toast');
      const toastMock = vi.mocked(useToast().toast);
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Error creating GitHub issues',
        description: 'Unknown error',
        variant: 'destructive'
      });
    });
  });

  describe('concurrent operations', () => {
    it('should handle multiple rapid refetch calls', async () => {
      let callCount = 0;
      (global.fetch as any).mockImplementation(async () => {
        callCount++;
        return {
          ok: true,
          json: async () => ({ ...mockProjectData, version: callCount })
        };
      });

      const { result } = renderHook(() => useProjectData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Trigger multiple refetches
      result.current.refetch();
      result.current.refetch();
      result.current.refetch();

      await waitFor(() => {
        expect(callCount).toBeGreaterThanOrEqual(4); // Initial + 3 refetches
      });
    });
  });
});