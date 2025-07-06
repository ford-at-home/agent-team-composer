import { useState, useEffect, useCallback, useRef } from 'react';
import { ProjectData } from '../types';
import { useToast } from './use-toast';

interface UseProjectDataOptions {
  maxRetries?: number;
  retryDelay?: number;
  apiUrl?: string;
}

interface UseProjectDataReturn {
  projectData: ProjectData | null;
  loading: boolean;
  error: string | null;
  updateProjectData: (data: ProjectData) => Promise<void>;
  createGitHubIssues: (phases: ProjectData['phases']) => Promise<any>;
  refetch: () => Promise<void>;
  retry: () => Promise<void>;
  isOnline: boolean;
  lastFetchTime: Date | null;
}

export function useProjectDataImproved(options: UseProjectDataOptions = {}): UseProjectDataReturn {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000'
  } = options;

  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastFetchTime, setLastFetchTime] = useState<Date | null>(null);
  
  const { toast } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Monitor online status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      toast({
        title: 'Connection restored',
        description: 'Syncing with server...',
      });
      refetch();
    };

    const handleOffline = () => {
      setIsOnline(false);
      toast({
        title: 'Connection lost',
        description: 'Working offline. Changes will sync when connection is restored.',
        variant: 'destructive'
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  const fetchProjectData = useCallback(async (isRetry = false) => {
    // Cancel any pending requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiUrl}/api/project`, {
        signal: abortControllerRef.current.signal,
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Project data not found. Please run the CLI tool first.');
        } else if (response.status >= 500) {
          throw new Error('Server error. Please try again later.');
        } else {
          throw new Error(`Failed to fetch project data (${response.status})`);
        }
      }
      
      const data = await response.json();
      
      // Validate response data
      if (!data.summary || !data.phases) {
        throw new Error('Invalid project data format');
      }
      
      setProjectData(data);
      setLastFetchTime(new Date());
      setRetryCount(0);
      
      // Cache in localStorage for offline access
      try {
        localStorage.setItem('project-data-cache', JSON.stringify(data));
        localStorage.setItem('project-data-cache-time', new Date().toISOString());
      } catch (e) {
        console.warn('Failed to cache project data:', e);
      }
      
    } catch (err) {
      // Handle abort errors
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Request aborted');
        return;
      }

      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);

      // Try to load from cache if available
      if (!isOnline || (isRetry && retryCount >= maxRetries)) {
        try {
          const cachedData = localStorage.getItem('project-data-cache');
          const cacheTime = localStorage.getItem('project-data-cache-time');
          
          if (cachedData) {
            const data = JSON.parse(cachedData);
            setProjectData(data);
            
            toast({
              title: 'Using cached data',
              description: cacheTime 
                ? `Last synced: ${new Date(cacheTime).toLocaleString()}`
                : 'Cached version loaded',
            });
            return;
          }
        } catch (e) {
          console.error('Failed to load cached data:', e);
        }
      }

      // Retry logic
      if (isOnline && retryCount < maxRetries && !isRetry) {
        const delay = retryDelay * Math.pow(2, retryCount); // Exponential backoff
        
        toast({
          title: 'Connection error',
          description: `Retrying in ${delay / 1000}s... (${retryCount + 1}/${maxRetries})`,
          variant: 'destructive'
        });

        setRetryCount(prev => prev + 1);
        
        retryTimeoutRef.current = setTimeout(() => {
          fetchProjectData(true);
        }, delay);
      } else {
        toast({
          title: 'Error loading project data',
          description: errorMessage,
          variant: 'destructive',
          action: {
            label: 'Retry',
            onClick: () => refetch()
          }
        });
      }
    } finally {
      setLoading(false);
    }
  }, [apiUrl, toast, isOnline, retryCount, maxRetries, retryDelay]);

  // Initial fetch
  useEffect(() => {
    fetchProjectData();
  }, []);

  const updateProjectData = useCallback(async (data: ProjectData) => {
    // Optimistic update
    const previousData = projectData;
    setProjectData(data);

    try {
      const response = await fetch(`${apiUrl}/api/project`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error('Failed to update project data');
      }

      // Update cache
      localStorage.setItem('project-data-cache', JSON.stringify(data));
      localStorage.setItem('project-data-cache-time', new Date().toISOString());
      
    } catch (err) {
      // Rollback on error
      setProjectData(previousData);
      
      // Store in pending updates for later sync
      try {
        const pendingUpdates = JSON.parse(
          localStorage.getItem('pending-updates') || '[]'
        );
        pendingUpdates.push({
          timestamp: new Date().toISOString(),
          data,
          type: 'update'
        });
        localStorage.setItem('pending-updates', JSON.stringify(pendingUpdates));
      } catch (e) {
        console.error('Failed to store pending update:', e);
      }

      toast({
        title: 'Error updating project data',
        description: isOnline 
          ? 'Failed to save changes. They will be synced when possible.'
          : 'You are offline. Changes will sync when connection is restored.',
        variant: 'destructive'
      });
      
      throw err;
    }
  }, [apiUrl, toast, isOnline, projectData]);

  const createGitHubIssues = useCallback(async (phases: ProjectData['phases']) => {
    try {
      setLoading(true);
      
      const response = await fetch(`${apiUrl}/api/github/create-issues`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phases })
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ details: 'Unknown error' }));
        
        if (response.status === 401) {
          throw new Error('GitHub authentication required. Please check your token.');
        } else if (response.status === 403) {
          throw new Error('GitHub API rate limit exceeded. Please try again later.');
        } else {
          throw new Error(error.details || 'Failed to create GitHub issues');
        }
      }
      
      const result = await response.json();
      
      toast({
        title: 'Success!',
        description: `Created ${result.epicsCreated || 0} epics and ${result.issuesCreated || 0} issues.`,
      });
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      
      toast({
        title: 'Error creating GitHub issues',
        description: errorMessage,
        variant: 'destructive'
      });
      
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiUrl, toast]);

  const refetch = useCallback(async () => {
    setRetryCount(0);
    await fetchProjectData();
  }, [fetchProjectData]);

  const retry = useCallback(async () => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    setRetryCount(0);
    await fetchProjectData();
  }, [fetchProjectData]);

  return {
    projectData,
    loading,
    error,
    updateProjectData,
    createGitHubIssues,
    refetch,
    retry,
    isOnline,
    lastFetchTime
  };
}