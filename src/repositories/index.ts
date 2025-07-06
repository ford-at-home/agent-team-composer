export * from './base.repository';
export * from './project.repository';
export * from './phase.repository';
export * from './issue.repository';

import { ProjectRepository } from './project.repository';
import { PhaseRepository } from './phase.repository';
import { IssueRepository } from './issue.repository';
import { PrismaClient } from '@prisma/client';

// Repository factory for dependency injection
export class RepositoryFactory {
  private prisma: PrismaClient;
  private projectRepo?: ProjectRepository;
  private phaseRepo?: PhaseRepository;
  private issueRepo?: IssueRepository;

  constructor(prismaClient: PrismaClient) {
    this.prisma = prismaClient;
  }

  get projects(): ProjectRepository {
    if (!this.projectRepo) {
      this.projectRepo = new ProjectRepository(this.prisma);
    }
    return this.projectRepo;
  }

  get phases(): PhaseRepository {
    if (!this.phaseRepo) {
      this.phaseRepo = new PhaseRepository(this.prisma);
    }
    return this.phaseRepo;
  }

  get issues(): IssueRepository {
    if (!this.issueRepo) {
      this.issueRepo = new IssueRepository(this.prisma);
    }
    return this.issueRepo;
  }
}

// Default singleton instances using the default prisma client
import { prisma } from '../database/client';

const defaultFactory = new RepositoryFactory(prisma);

export const projectRepository = defaultFactory.projects;
export const phaseRepository = defaultFactory.phases;
export const issueRepository = defaultFactory.issues;