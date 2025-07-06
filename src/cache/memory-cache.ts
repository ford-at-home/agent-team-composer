import NodeCache from 'node-cache';
import { CacheInterface, CacheConfig } from './cache-interface';

export class MemoryCache implements CacheInterface {
  private cache: NodeCache;
  private config: CacheConfig;

  constructor(config: CacheConfig = {}) {
    this.config = {
      prefix: config.prefix || 'pdn:',
      ttl: config.ttl || 3600,
      serialize: config.serialize || JSON.stringify,
      deserialize: config.deserialize || JSON.parse
    };

    this.cache = new NodeCache({
      stdTTL: this.config.ttl,
      checkperiod: 600,
      useClones: false
    });
  }

  private getKey(key: string): string {
    return `${this.config.prefix}${key}`;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const fullKey = this.getKey(key);
      const value = this.cache.get<string>(fullKey);
      
      if (value === undefined) {
        return null;
      }

      return this.config.deserialize!(value) as T;
    } catch (error) {
      console.error('Memory cache get error:', error);
      return null;
    }
  }

  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    try {
      const fullKey = this.getKey(key);
      const serialized = this.config.serialize!(value);
      
      if (ttl) {
        this.cache.set(fullKey, serialized, ttl);
      } else {
        this.cache.set(fullKey, serialized);
      }
    } catch (error) {
      console.error('Memory cache set error:', error);
      throw error;
    }
  }

  async del(key: string): Promise<void> {
    const fullKey = this.getKey(key);
    this.cache.del(fullKey);
  }

  async delMany(pattern: string): Promise<void> {
    const keys = await this.keys(pattern);
    if (keys.length > 0) {
      this.cache.del(keys);
    }
  }

  async exists(key: string): Promise<boolean> {
    const fullKey = this.getKey(key);
    return this.cache.has(fullKey);
  }

  async ttl(key: string): Promise<number> {
    const fullKey = this.getKey(key);
    const ttl = this.cache.getTtl(fullKey);
    
    if (!ttl) {
      return -1;
    }
    
    const now = Date.now();
    return Math.max(0, Math.floor((ttl - now) / 1000));
  }

  async expire(key: string, ttl: number): Promise<void> {
    const fullKey = this.getKey(key);
    const value = this.cache.get(fullKey);
    
    if (value !== undefined) {
      this.cache.set(fullKey, value, ttl);
    }
  }

  async flush(): Promise<void> {
    this.cache.flushAll();
  }

  async keys(pattern: string): Promise<string[]> {
    const allKeys = this.cache.keys();
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    
    return allKeys.filter(key => regex.test(key));
  }
}