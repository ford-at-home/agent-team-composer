import { PrismaClient } from '@prisma/client';
import { prisma } from '../database/client';

export interface Repository<T> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  create(data: any): Promise<T>;
  update(id: string, data: any): Promise<T>;
  delete(id: string): Promise<boolean>;
}

export abstract class BaseRepository<T> implements Repository<T> {
  protected prisma: PrismaClient;

  constructor(prismaClient?: PrismaClient) {
    this.prisma = prismaClient || prisma;
  }

  abstract findById(id: string): Promise<T | null>;
  abstract findAll(): Promise<T[]>;
  abstract create(data: any): Promise<T>;
  abstract update(id: string, data: any): Promise<T>;
  abstract delete(id: string): Promise<boolean>;

  // Pagination helper
  protected paginate(page: number = 1, limit: number = 10) {
    const skip = (page - 1) * limit;
    return { skip, take: limit };
  }

  // Audit log helper
  protected async createAuditLog(
    entityType: string,
    entityId: string,
    action: string,
    changes?: any,
    userId?: string
  ): Promise<void> {
    await this.prisma.auditLog.create({
      data: {
        entityType,
        entityId,
        action,
        changes,
        userId
      }
    });
  }
}