import { config } from 'dotenv';
import { expand } from 'dotenv-expand';

// Load environment variables
const myEnv = config();
expand(myEnv);

export interface DatabaseConfig {
  provider: 'sqlite' | 'postgresql';
  url: string;
  poolSize?: number;
  connectionTimeout?: number;
  queryTimeout?: number;
}

export function getDatabaseConfig(): DatabaseConfig {
  const provider = (process.env.DATABASE_PROVIDER as 'sqlite' | 'postgresql') || 'sqlite';
  
  // Default URLs based on provider
  const defaultUrls = {
    sqlite: 'file:./dev.db',
    postgresql: 'postgresql://localhost:5432/project_navigator'
  };
  
  const url = process.env.DATABASE_URL || defaultUrls[provider];
  
  return {
    provider,
    url,
    poolSize: parseInt(process.env.DATABASE_POOL_SIZE || '10', 10),
    connectionTimeout: parseInt(process.env.DATABASE_CONNECTION_TIMEOUT || '5000', 10),
    queryTimeout: parseInt(process.env.DATABASE_QUERY_TIMEOUT || '30000', 10)
  };
}

export function getCacheConfig() {
  return {
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379', 10),
      password: process.env.REDIS_PASSWORD,
      db: parseInt(process.env.REDIS_DB || '0', 10),
      ttl: parseInt(process.env.CACHE_TTL || '3600', 10) // Default 1 hour
    },
    memory: {
      checkPeriod: 600, // Check for expired entries every 10 minutes
      stdTTL: parseInt(process.env.CACHE_TTL || '3600', 10),
      maxKeys: 1000
    }
  };
}