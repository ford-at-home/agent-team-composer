import { Project, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';
import { getCache, cacheKeys, invalidateProjectCache } from '../cache';
import { ProjectData, ProjectSummary } from '../types';

export interface ProjectWithRelations extends Project {
  phases: any[];
}

export class ProjectRepository extends BaseRepository<Project> {
  private cache = getCache();

  async findById(id: string): Promise<ProjectWithRelations | null> {
    const cacheKey = cacheKeys.project(id);
    const cached = await this.cache.get<ProjectWithRelations>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const project = await this.prisma.project.findUnique({
      where: { id },
      include: {
        phases: {
          orderBy: { order: 'asc' },
          include: {
            issues: true,
            roles: true
          }
        }
      }
    });

    if (project) {
      await this.cache.set(cacheKey, project, 3600); // Cache for 1 hour
    }

    return project;
  }

  async findByRepository(repository: string, branch: string = 'main'): Promise<ProjectWithRelations | null> {
    const cacheKey = cacheKeys.projectByRepo(repository, branch);
    const cached = await this.cache.get<ProjectWithRelations>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const project = await this.prisma.project.findUnique({
      where: {
        repository_branch: {
          repository,
          branch
        }
      },
      include: {
        phases: {
          orderBy: { order: 'asc' },
          include: {
            issues: true,
            roles: true
          }
        }
      }
    });

    if (project) {
      await this.cache.set(cacheKey, project, 3600);
    }

    return project;
  }

  async findAll(): Promise<Project[]> {
    const cacheKey = cacheKeys.allProjects();
    const cached = await this.cache.get<Project[]>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const projects = await this.prisma.project.findMany({
      orderBy: { createdAt: 'desc' }
    });

    await this.cache.set(cacheKey, projects, 300); // Cache for 5 minutes
    return projects;
  }

  async findPaginated(page: number = 1, limit: number = 10): Promise<{
    data: Project[];
    total: number;
    page: number;
    limit: number;
  }> {
    const cacheKey = cacheKeys.projectsList(page, limit);
    const cached = await this.cache.get<any>(cacheKey);
    
    if (cached) {
      return cached;
    }

    const { skip, take } = this.paginate(page, limit);
    
    const [data, total] = await Promise.all([
      this.prisma.project.findMany({
        skip,
        take,
        orderBy: { createdAt: 'desc' }
      }),
      this.prisma.project.count()
    ]);

    const result = { data, total, page, limit };
    await this.cache.set(cacheKey, result, 300);
    
    return result;
  }

  async create(data: Prisma.ProjectCreateInput): Promise<Project> {
    const project = await this.prisma.project.create({
      data
    });

    await this.createAuditLog('project', project.id, 'create', data);
    await this.cache.delMany('projects:*');

    return project;
  }

  async createFromProjectData(projectData: ProjectData): Promise<ProjectWithRelations> {
    const { summary, phases } = projectData;

    const project = await this.prisma.project.create({
      data: {
        title: summary.title,
        description: summary.description,
        domain: summary.domain,
        repository: summary.repository,
        branch: summary.branch,
        phases: {
          create: phases.map((phase, index) => ({
            title: phase.title,
            description: phase.description,
            order: index,
            approved: phase.approved,
            roles: {
              create: phase.roles.map(role => ({ role }))
            },
            issues: {
              create: phase.issues.map(issue => ({
                title: issue.title,
                description: issue.description,
                role: issue.role
              }))
            }
          }))
        }
      },
      include: {
        phases: {
          include: {
            issues: true,
            roles: true
          }
        }
      }
    });

    await this.createAuditLog('project', project.id, 'create', projectData);
    await this.cache.delMany('projects:*');

    return project;
  }

  async update(id: string, data: Prisma.ProjectUpdateInput): Promise<Project> {
    const existing = await this.findById(id);
    
    const project = await this.prisma.project.update({
      where: { id },
      data
    });

    await this.createAuditLog('project', project.id, 'update', {
      before: existing,
      after: data
    });
    
    await invalidateProjectCache(id);

    return project;
  }

  async updateFromProjectData(id: string, projectData: ProjectData): Promise<ProjectWithRelations> {
    const { summary, phases } = projectData;

    // Use transaction for atomic updates
    const project = await this.prisma.$transaction(async (tx) => {
      // Update project
      await tx.project.update({
        where: { id },
        data: {
          title: summary.title,
          description: summary.description,
          domain: summary.domain,
          repository: summary.repository,
          branch: summary.branch
        }
      });

      // Delete existing phases and related data (cascade will handle issues and roles)
      await tx.phase.deleteMany({
        where: { projectId: id }
      });

      // Create new phases
      for (let i = 0; i < phases.length; i++) {
        const phase = phases[i];
        await tx.phase.create({
          data: {
            projectId: id,
            title: phase.title,
            description: phase.description,
            order: i,
            approved: phase.approved,
            roles: {
              create: phase.roles.map(role => ({ role }))
            },
            issues: {
              create: phase.issues.map(issue => ({
                title: issue.title,
                description: issue.description,
                role: issue.role
              }))
            }
          }
        });
      }

      // Return updated project with relations
      return await tx.project.findUnique({
        where: { id },
        include: {
          phases: {
            orderBy: { order: 'asc' },
            include: {
              issues: true,
              roles: true
            }
          }
        }
      });
    });

    if (!project) {
      throw new Error('Failed to update project');
    }

    await this.createAuditLog('project', project.id, 'update', projectData);
    await invalidateProjectCache(id);

    return project;
  }

  async delete(id: string): Promise<boolean> {
    try {
      await this.prisma.project.delete({
        where: { id }
      });

      await this.createAuditLog('project', id, 'delete');
      await invalidateProjectCache(id);
      
      return true;
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === 'P2025') {
        return false; // Record not found
      }
      throw error;
    }
  }

  async search(query: string): Promise<Project[]> {
    return this.prisma.project.findMany({
      where: {
        OR: [
          { title: { contains: query, mode: 'insensitive' } },
          { description: { contains: query, mode: 'insensitive' } },
          { repository: { contains: query, mode: 'insensitive' } }
        ]
      },
      orderBy: { createdAt: 'desc' }
    });
  }
}