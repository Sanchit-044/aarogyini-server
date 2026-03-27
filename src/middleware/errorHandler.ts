import { Request, Response, NextFunction } from 'express';
import { AppError } from '../utils/AppError';
import { logger } from '../utils/logger';
import { config } from '../config/env';

const handleCastError = (err: any): AppError =>
  new AppError(`Invalid ${err.path}: ${err.value}`, 400);

const handleDuplicateKey = (err: any): AppError => {
  const field = Object.keys(err.keyValue)[0];
  return new AppError(`${field} already exists`, 409);
};

const handleValidationError = (err: any): AppError => {
  const messages = Object.values(err.errors).map((e: any) => e.message);
  return new AppError(messages.join('. '), 422);
};

const handleJwtError = (): AppError => new AppError('Invalid token', 401);
const handleJwtExpired = (): AppError => new AppError('Token expired, please log in again', 401);

export const globalErrorHandler = (
  err: any,
  _req: Request,
  res: Response,
  _next: NextFunction
): void => {
  err.statusCode = err.statusCode || 500;

  let error = err instanceof AppError ? err : new AppError(err.message, err.statusCode);

  if (err.name === 'CastError') error = handleCastError(err);
  if (err.code === 11000) error = handleDuplicateKey(err);
  if (err.name === 'ValidationError') error = handleValidationError(err);
  if (err.name === 'JsonWebTokenError') error = handleJwtError();
  if (err.name === 'TokenExpiredError') error = handleJwtExpired();

  if (!error.isOperational) {
    logger.error('Unhandled error:', err);
  }

  res.status(error.statusCode).json({
    success: false,
    message: error.message,
    ...(config.app.isDev && { stack: err.stack }),
  });
};

export const notFoundHandler = (req: Request, res: Response): void => {
  res.status(404).json({ success: false, message: `Route ${req.originalUrl} not found` });
};
