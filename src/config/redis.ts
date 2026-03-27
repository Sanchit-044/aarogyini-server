import Redis from 'ioredis';
import { config } from './env';
import { logger } from '../utils/logger';

let redisClient: Redis | null = null;

export const connectRedis = (): Redis => {
  if (redisClient) return redisClient;

  redisClient = new Redis({
    host: config.redis.host,
    port: config.redis.port,
    password: config.redis.password,
    retryStrategy: (times) => {
      if (times > 3) {
        logger.error('Redis: Could not connect after 3 retries');
        return null;
      }
      return Math.min(times * 200, 2000);
    },
    lazyConnect: false,
  });

  redisClient.on('connect', () => logger.info('Redis connected'));
  redisClient.on('error', (err) => logger.error(`Redis error: ${err.message}`));
  redisClient.on('close', () => logger.warn('Redis connection closed'));

  return redisClient;
};

export const getRedis = (): Redis => {
  if (!redisClient) return connectRedis();
  return redisClient;
};

// Cache helpers
export const cacheGet = async <T>(key: string): Promise<T | null> => {
  const client = getRedis();
  const data = await client.get(key);
  return data ? (JSON.parse(data) as T) : null;
};

export const cacheSet = async (
  key: string,
  value: unknown,
  ttl = config.redis.ttl
): Promise<void> => {
  const client = getRedis();
  await client.set(key, JSON.stringify(value), 'EX', ttl);
};

export const cacheDel = async (key: string): Promise<void> => {
  const client = getRedis();
  await client.del(key);
};

export const cacheDelPattern = async (pattern: string): Promise<void> => {
  const client = getRedis();
  const keys = await client.keys(pattern);
  if (keys.length > 0) await client.del(...keys);
};
