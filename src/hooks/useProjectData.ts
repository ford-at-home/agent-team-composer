import { useState, useEffect } from 'react';
import { ProjectData } from '../types';
import { useToast } from './use-toast';

export function useProjectData() {
  const [projectData, setProjectData] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchProjectData();
  }, []);

  const fetchProjectData = async () => {
    try {
      setLoading(true);
      const apiUrl = import.meta.env.DEV ? 'http://localhost:3000/api/project' : '/api/project';
      const response = await fetch(apiUrl);
      
      if (!response.ok) {
        throw new Error('Failed to fetch project data');
      }
      
      const data = await response.json();
      setProjectData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      toast({
        title: 'Error loading project data',
        description: 'Please ensure the CLI tool is running',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const updateProjectData = async (data: ProjectData) => {
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:3000/api/project' : '/api/project';
      const response = await fetch(apiUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error('Failed to update project data');
      }
      
      setProjectData(data);
    } catch (err) {
      toast({
        title: 'Error updating project data',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive'
      });
      throw err;
    }
  };

  const createGitHubIssues = async (phases: ProjectData['phases']) => {
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:3000/api/github/create-issues' : '/api/github/create-issues';
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phases })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.details || 'Failed to create GitHub issues');
      }
      
      const result = await response.json();
      return result;
    } catch (err) {
      toast({
        title: 'Error creating GitHub issues',
        description: err instanceof Error ? err.message : 'Unknown error',
        variant: 'destructive'
      });
      throw err;
    }
  };

  return {
    projectData,
    loading,
    error,
    updateProjectData,
    createGitHubIssues,
    refetch: fetchProjectData
  };
}