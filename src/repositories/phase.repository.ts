import { Phase, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';
import { getCache, cacheKeys, invalidatePhaseCache } from '../cache';

export interface PhaseWithRelations extends Phase {
  issues: any[];
  roles: any[];
}

export class PhaseRepository extends BaseRepository<Phase> {
  private cache = getCache();

  async findById(id: string): Promise<PhaseWithRelations | null> {
    const cacheKey = cacheKeys.phase(id);
    const cached = await this.cache.get<PhaseWithRelations>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const phase = await this.prisma.phase.findUnique({
      where: { id },
      include: {
        issues: true,
        roles: true,
        project: true
      }
    });

    if (phase) {
      await this.cache.set(cacheKey, phase, 3600);
    }

    return phase;
  }

  async findByProjectId(projectId: string): Promise<PhaseWithRelations[]> {
    const cacheKey = cacheKeys.phasesForProject(projectId);
    const cached = await this.cache.get<PhaseWithRelations[]>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const phases = await this.prisma.phase.findMany({
      where: { projectId },
      orderBy: { order: 'asc' },
      include: {
        issues: true,
        roles: true
      }
    });

    await this.cache.set(cacheKey, phases, 3600);
    return phases;
  }

  async findAll(): Promise<Phase[]> {
    return this.prisma.phase.findMany({
      orderBy: [
        { projectId: 'asc' },
        { order: 'asc' }
      ]
    });
  }

  async create(data: Prisma.PhaseCreateInput): Promise<Phase> {
    const phase = await this.prisma.phase.create({
      data
    });

    await this.createAuditLog('phase', phase.id, 'create', data);
    await invalidatePhaseCache(phase.id, phase.projectId);

    return phase;
  }

  async update(id: string, data: Prisma.PhaseUpdateInput): Promise<Phase> {
    const existing = await this.findById(id);
    
    const phase = await this.prisma.phase.update({
      where: { id },
      data
    });

    await this.createAuditLog('phase', phase.id, 'update', {
      before: existing,
      after: data
    });
    
    await invalidatePhaseCache(id, phase.projectId);

    return phase;
  }

  async approve(id: string): Promise<Phase> {
    const phase = await this.update(id, { approved: true });
    
    await this.createAuditLog('phase', phase.id, 'approve');
    
    return phase;
  }

  async unapprove(id: string): Promise<Phase> {
    const phase = await this.update(id, { approved: false });
    
    await this.createAuditLog('phase', phase.id, 'unapprove');
    
    return phase;
  }

  async delete(id: string): Promise<boolean> {
    try {
      const phase = await this.findById(id);
      if (!phase) {
        return false;
      }

      await this.prisma.phase.delete({
        where: { id }
      });

      await this.createAuditLog('phase', id, 'delete');
      await invalidatePhaseCache(id, phase.projectId);
      
      return true;
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2025') {
        return false;
      }
      throw error;
    }
  }

  async reorder(projectId: string, phaseIds: string[]): Promise<Phase[]> {
    const updates = phaseIds.map((id, index) => 
      this.prisma.phase.update({
        where: { id },
        data: { order: index }
      })
    );

    const phases = await this.prisma.$transaction(updates);

    await this.createAuditLog('phase', projectId, 'reorder', { phaseIds });
    await this.cache.del(cacheKeys.phasesForProject(projectId));

    return phases;
  }

  async addRole(phaseId: string, role: string): Promise<void> {
    await this.prisma.phaseRole.create({
      data: {
        phaseId,
        role
      }
    });

    await invalidatePhaseCache(phaseId, (await this.findById(phaseId))!.projectId);
  }

  async removeRole(phaseId: string, role: string): Promise<void> {
    await this.prisma.phaseRole.delete({
      where: {
        phaseId_role: {
          phaseId,
          role
        }
      }
    });

    await invalidatePhaseCache(phaseId, (await this.findById(phaseId))!.projectId);
  }
}