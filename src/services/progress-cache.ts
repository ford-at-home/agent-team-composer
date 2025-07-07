import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';
import crypto from 'crypto';

import { Phase, LLMPhaseGeneration, LLMEpicGeneration } from '../types';

export interface ProgressData {
  projectInfo: {
    title: string;
    description: string;
    domain: string;
    features: string[];
    techStack: string[];
    complexity: string;
    targetUsers?: string[];
  };
  readmeContent: string;
  phases?: LLMPhaseGeneration['phases'];
  phasesWithTasks?: Array<Phase & { tasks: LLMEpicGeneration['tasks'] }>;
  finalPhases?: Phase[];
  timestamp: number;
}

export class ProgressCache {
  private cacheDir: string;
  private cacheFile: string;
  
  constructor(projectTitle: string) {
    // Create a unique cache file based on project title
    const hash = crypto.createHash('md5').update(projectTitle).digest('hex');
    this.cacheDir = path.join(os.tmpdir(), 'agent-team-composer-cache');
    this.cacheFile = path.join(this.cacheDir, `progress-${hash}.json`);
  }
  
  async ensureCacheDir(): Promise<void> {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true });
    } catch (error) {
      console.warn('Failed to create cache directory:', error);
    }
  }
  
  async save(data: Partial<ProgressData>): Promise<void> {
    try {
      await this.ensureCacheDir();
      
      // Load existing data
      const existing = await this.load();
      
      // Merge with new data
      const updated = {
        ...existing,
        ...data,
        timestamp: Date.now()
      };
      
      // Save to file
      await fs.writeFile(this.cacheFile, JSON.stringify(updated, null, 2));
      console.log(`💾 Progress saved to cache: ${this.cacheFile}`);
    } catch (error) {
      console.warn('Failed to save progress:', error);
    }
  }
  
  async load(): Promise<ProgressData | null> {
    try {
      const content = await fs.readFile(this.cacheFile, 'utf8');
      const data = JSON.parse(content) as ProgressData;
      
      // Check if cache is still valid (24 hours)
      const maxAge = 24 * 60 * 60 * 1000;
      if (Date.now() - data.timestamp > maxAge) {
        console.log('⚠️  Cache is older than 24 hours, ignoring...');
        return null;
      }
      
      console.log(`📂 Loaded progress from cache (${new Date(data.timestamp).toLocaleString()})`);
      return data;
    } catch (error) {
      // Cache doesn't exist or is invalid
      return null;
    }
  }
  
  async clear(): Promise<void> {
    try {
      await fs.unlink(this.cacheFile);
      console.log('🗑️  Cache cleared');
    } catch (error) {
      // Ignore if file doesn't exist
    }
  }
  
  getCachePath(): string {
    return this.cacheFile;
  }
}