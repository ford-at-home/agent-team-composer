import Redis from 'ioredis';
import { CacheInterface, CacheConfig } from './cache-interface';
import { getCacheConfig } from '../database/config';

export class RedisCache implements CacheInterface {
  private client: Redis;
  private config: CacheConfig;

  constructor(config: CacheConfig = {}) {
    const redisConfig = getCacheConfig().redis;
    
    this.config = {
      prefix: config.prefix || 'pdn:',
      ttl: config.ttl || redisConfig.ttl,
      serialize: config.serialize || JSON.stringify,
      deserialize: config.deserialize || JSON.parse
    };

    this.client = new Redis({
      host: redisConfig.host,
      port: redisConfig.port,
      password: redisConfig.password,
      db: redisConfig.db,
      retryStrategy: (times: number) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
      maxRetriesPerRequest: 3
    });

    this.client.on('error', (error) => {
      console.error('Redis error:', error);
    });

    this.client.on('connect', () => {
      console.log('Redis connected successfully');
    });
  }

  private getKey(key: string): string {
    return `${this.config.prefix}${key}`;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const fullKey = this.getKey(key);
      const value = await this.client.get(fullKey);
      
      if (!value) {
        return null;
      }

      return this.config.deserialize!(value) as T;
    } catch (error) {
      console.error('Redis cache get error:', error);
      return null;
    }
  }

  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    try {
      const fullKey = this.getKey(key);
      const serialized = this.config.serialize!(value);
      const expiry = ttl || this.config.ttl;
      
      if (expiry) {
        await this.client.setex(fullKey, expiry, serialized);
      } else {
        await this.client.set(fullKey, serialized);
      }
    } catch (error) {
      console.error('Redis cache set error:', error);
      throw error;
    }
  }

  async del(key: string): Promise<void> {
    const fullKey = this.getKey(key);
    await this.client.del(fullKey);
  }

  async delMany(pattern: string): Promise<void> {
    const keys = await this.keys(pattern);
    if (keys.length > 0) {
      await this.client.del(...keys);
    }
  }

  async exists(key: string): Promise<boolean> {
    const fullKey = this.getKey(key);
    const exists = await this.client.exists(fullKey);
    return exists === 1;
  }

  async ttl(key: string): Promise<number> {
    const fullKey = this.getKey(key);
    return await this.client.ttl(fullKey);
  }

  async expire(key: string, ttl: number): Promise<void> {
    const fullKey = this.getKey(key);
    await this.client.expire(fullKey, ttl);
  }

  async flush(): Promise<void> {
    const keys = await this.keys('*');
    if (keys.length > 0) {
      await this.client.del(...keys);
    }
  }

  async keys(pattern: string): Promise<string[]> {
    const fullPattern = this.getKey(pattern);
    return await this.client.keys(fullPattern);
  }

  async disconnect(): Promise<void> {
    await this.client.quit();
  }
}