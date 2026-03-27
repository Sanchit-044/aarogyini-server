import express, { Application } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import mongoSanitize from 'express-mongo-sanitize';
import cookieParser from 'cookie-parser';

import { config } from './config/env';
import { logger } from './utils/logger';
import router from './routes';
import { globalErrorHandler, notFoundHandler } from './middleware/errorHandler';

export const createApp = (): Application => {
  const app = express();

  // ── Security headers ────────────────────────────────────────────────────────
  app.use(helmet());

  // ── CORS ────────────────────────────────────────────────────────────────────
  app.use(
    cors({
      origin: (origin, cb) => {
        if (!origin || config.cors.origins.includes(origin)) return cb(null, true);
        cb(new Error(`CORS: origin ${origin} not allowed`));
      },
      credentials: true,
      methods: ['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
    })
  );

  // ── Body parsers ─────────────────────────────────────────────────────────────
  app.use(express.json({ limit: '10kb' }));
  app.use(express.urlencoded({ extended: true, limit: '10kb' }));
  app.use(cookieParser());

  // ── Sanitize MongoDB operators in request body/params ────────────────────────
  app.use(mongoSanitize());

  // ── Compression ──────────────────────────────────────────────────────────────
  app.use(compression());

  // ── HTTP request logging ─────────────────────────────────────────────────────
  if (config.app.isDev) {
    app.use(morgan('dev'));
  } else {
    app.use(
      morgan('combined', {
        stream: { write: (msg) => logger.info(msg.trim()) },
      })
    );
  }

  // ── Global rate limiter ──────────────────────────────────────────────────────
  app.use(
    '/api',
    rateLimit({
      windowMs: config.rateLimit.windowMs,
      max: config.rateLimit.max,
      standardHeaders: true,
      legacyHeaders: false,
      message: { success: false, message: 'Too many requests, please try again later.' },
    })
  );

  // ── Stricter rate limit for auth endpoints ───────────────────────────────────
  app.use(
    '/api/auth',
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 min
      max: 20,
      message: { success: false, message: 'Too many auth attempts. Try again in 15 minutes.' },
    })
  );

  // ── Routes ───────────────────────────────────────────────────────────────────
  app.use('/api', router);

  // ── 404 handler ──────────────────────────────────────────────────────────────
  app.use(notFoundHandler);

  // ── Global error handler ─────────────────────────────────────────────────────
  app.use(globalErrorHandler);

  return app;
};
