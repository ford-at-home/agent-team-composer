import { CacheInterface } from './cache-interface';
import { MemoryCache } from './memory-cache';
import { RedisCache } from './redis-cache';

let cacheInstance: CacheInterface | null = null;

export function getCache(): CacheInterface {
  if (!cacheInstance) {
    // Try Redis first, fall back to memory cache
    if (process.env.REDIS_HOST) {
      try {
        cacheInstance = new RedisCache();
        console.log('Using Redis cache');
      } catch (error) {
        console.warn('Failed to initialize Redis cache, falling back to memory cache:', error);
        cacheInstance = new MemoryCache();
      }
    } else {
      cacheInstance = new MemoryCache();
      console.log('Using memory cache');
    }
  }

  return cacheInstance;
}

// Cache key generators
export const cacheKeys = {
  project: (id: string) => `project:${id}`,
  projectByRepo: (repo: string, branch: string) => `project:repo:${repo}:${branch}`,
  phase: (id: string) => `phase:${id}`,
  phasesForProject: (projectId: string) => `phases:project:${projectId}`,
  issue: (id: string) => `issue:${id}`,
  issuesForPhase: (phaseId: string) => `issues:phase:${phaseId}`,
  allProjects: () => 'projects:all',
  projectsList: (page: number, limit: number) => `projects:list:${page}:${limit}`
};

// Cache invalidation helpers
export async function invalidateProjectCache(projectId: string): Promise<void> {
  const cache = getCache();
  await cache.del(cacheKeys.project(projectId));
  await cache.delMany(`phases:project:${projectId}*`);
  await cache.delMany('projects:*');
}

export async function invalidatePhaseCache(phaseId: string, projectId: string): Promise<void> {
  const cache = getCache();
  await cache.del(cacheKeys.phase(phaseId));
  await cache.del(cacheKeys.phasesForProject(projectId));
  await cache.delMany(`issues:phase:${phaseId}*`);
  await invalidateProjectCache(projectId);
}

export async function invalidateIssueCache(issueId: string, phaseId: string, projectId: string): Promise<void> {
  const cache = getCache();
  await cache.del(cacheKeys.issue(issueId));
  await cache.del(cacheKeys.issuesForPhase(phaseId));
  await invalidatePhaseCache(phaseId, projectId);
}