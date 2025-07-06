export interface CacheInterface {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  del(key: string): Promise<void>;
  delMany(pattern: string): Promise<void>;
  exists(key: string): Promise<boolean>;
  ttl(key: string): Promise<number>;
  expire(key: string, ttl: number): Promise<void>;
  flush(): Promise<void>;
  keys(pattern: string): Promise<string[]>;
}

export interface CacheConfig {
  prefix?: string;
  ttl?: number;
  serialize?: (value: any) => string;
  deserialize?: (value: string) => any;
}