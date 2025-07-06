import { Issue, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';
import { getCache, cacheKeys, invalidateIssueCache } from '../cache';

export interface IssueWithRelations extends Issue {
  phase: any;
}

export class IssueRepository extends BaseRepository<Issue> {
  private cache = getCache();

  async findById(id: string): Promise<IssueWithRelations | null> {
    const cacheKey = cacheKeys.issue(id);
    const cached = await this.cache.get<IssueWithRelations>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const issue = await this.prisma.issue.findUnique({
      where: { id },
      include: {
        phase: {
          include: {
            project: true
          }
        }
      }
    });

    if (issue) {
      await this.cache.set(cacheKey, issue, 3600);
    }

    return issue;
  }

  async findByPhaseId(phaseId: string): Promise<Issue[]> {
    const cacheKey = cacheKeys.issuesForPhase(phaseId);
    const cached = await this.cache.get<Issue[]>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const issues = await this.prisma.issue.findMany({
      where: { phaseId },
      orderBy: { createdAt: 'asc' }
    });

    await this.cache.set(cacheKey, issues, 3600);
    return issues;
  }

  async findAll(): Promise<Issue[]> {
    return this.prisma.issue.findMany({
      orderBy: { createdAt: 'desc' }
    });
  }

  async findByStatus(status: string): Promise<Issue[]> {
    return this.prisma.issue.findMany({
      where: { status },
      orderBy: { createdAt: 'desc' },
      include: {
        phase: {
          include: {
            project: true
          }
        }
      }
    });
  }

  async findByGitHubId(githubId: number): Promise<Issue | null> {
    return this.prisma.issue.findFirst({
      where: { githubId }
    });
  }

  async create(data: Prisma.IssueCreateInput): Promise<Issue> {
    const issue = await this.prisma.issue.create({
      data
    });

    const phase = await this.prisma.phase.findUnique({
      where: { id: issue.phaseId },
      select: { projectId: true }
    });

    await this.createAuditLog('issue', issue.id, 'create', data);
    await invalidateIssueCache(issue.id, issue.phaseId, phase!.projectId);

    return issue;
  }

  async createBatch(issues: Prisma.IssueCreateManyInput[]): Promise<number> {
    const result = await this.prisma.issue.createMany({
      data: issues
    });

    // Invalidate cache for affected phases
    const phaseIds = [...new Set(issues.map(i => i.phaseId))];
    for (const phaseId of phaseIds) {
      await this.cache.del(cacheKeys.issuesForPhase(phaseId));
    }

    return result.count;
  }

  async update(id: string, data: Prisma.IssueUpdateInput): Promise<Issue> {
    const existing = await this.findById(id);
    
    const issue = await this.prisma.issue.update({
      where: { id },
      data
    });

    await this.createAuditLog('issue', issue.id, 'update', {
      before: existing,
      after: data
    });
    
    const phase = await this.prisma.phase.findUnique({
      where: { id: issue.phaseId },
      select: { projectId: true }
    });

    await invalidateIssueCache(id, issue.phaseId, phase!.projectId);

    return issue;
  }

  async updateStatus(id: string, status: string): Promise<Issue> {
    return this.update(id, { status });
  }

  async updateGitHubInfo(id: string, githubId: number, githubUrl: string): Promise<Issue> {
    return this.update(id, { 
      githubId, 
      githubUrl,
      status: 'created'
    });
  }

  async delete(id: string): Promise<boolean> {
    try {
      const issue = await this.findById(id);
      if (!issue) {
        return false;
      }

      await this.prisma.issue.delete({
        where: { id }
      });

      const phase = await this.prisma.phase.findUnique({
        where: { id: issue.phaseId },
        select: { projectId: true }
      });

      await this.createAuditLog('issue', id, 'delete');
      await invalidateIssueCache(id, issue.phaseId, phase!.projectId);
      
      return true;
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2025') {
        return false;
      }
      throw error;
    }
  }

  async getStatsByProject(projectId: string): Promise<{
    total: number;
    byStatus: Record<string, number>;
    byPhase: Record<string, number>;
  }> {
    const issues = await this.prisma.issue.findMany({
      where: {
        phase: {
          projectId
        }
      },
      include: {
        phase: {
          select: {
            id: true,
            title: true
          }
        }
      }
    });

    const stats = {
      total: issues.length,
      byStatus: {} as Record<string, number>,
      byPhase: {} as Record<string, number>
    };

    issues.forEach(issue => {
      // Count by status
      stats.byStatus[issue.status] = (stats.byStatus[issue.status] || 0) + 1;
      
      // Count by phase
      stats.byPhase[issue.phase.title] = (stats.byPhase[issue.phase.title] || 0) + 1;
    });

    return stats;
  }
}