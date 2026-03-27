import { createApp } from './app';
import { connectDB } from './config/database';
import { connectRedis } from './config/redis';
import { config } from './config/env';
import { logger } from './utils/logger';

const start = async (): Promise<void> => {
  // Connect to services
  await connectDB();
  connectRedis();

  const app = createApp();

  const server = app.listen(config.app.port, () => {
    logger.info(`🚀 ${config.app.name} running on port ${config.app.port} [${config.app.env}]`);
  });

  // ── Graceful shutdown ────────────────────────────────────────────────────────
  const shutdown = (signal: string) => {
    logger.info(`${signal} received. Shutting down gracefully...`);
    server.close(() => {
      logger.info('HTTP server closed');
      process.exit(0);
    });
    setTimeout(() => {
      logger.error('Forced shutdown after timeout');
      process.exit(1);
    }, 10_000);
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  process.on('unhandledRejection', (reason) => {
    logger.error('Unhandled Rejection:', reason);
    shutdown('unhandledRejection');
  });

  process.on('uncaughtException', (err) => {
    logger.error('Uncaught Exception:', err);
    shutdown('uncaughtException');
  });
};

start();
