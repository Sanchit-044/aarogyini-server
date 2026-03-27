import { Response } from 'express';
import { ApiResponse } from '../types';

export const sendSuccess = <T>(
  res: Response,
  data: T,
  message = 'Success',
  statusCode = 200,
  meta?: ApiResponse['meta']
): Response => {
  const response: ApiResponse<T> = { success: true, message, data, ...(meta && { meta }) };
  return res.status(statusCode).json(response);
};

export const sendCreated = <T>(res: Response, data: T, message = 'Created successfully'): Response =>
  sendSuccess(res, data, message, 201);

export const sendError = (
  res: Response,
  message: string,
  statusCode = 400,
  errors?: string[]
): Response => {
  const response: ApiResponse = { success: false, message, ...(errors && { errors }) };
  return res.status(statusCode).json(response);
};

export const sendNotFound = (res: Response, resource = 'Resource'): Response =>
  sendError(res, `${resource} not found`, 404);

export const sendUnauthorized = (res: Response, message = 'Unauthorized'): Response =>
  sendError(res, message, 401);

export const sendForbidden = (res: Response, message = 'Forbidden'): Response =>
  sendError(res, message, 403);

export const getPaginationMeta = (
  total: number,
  page: number,
  limit: number
): ApiResponse['meta'] => ({
  total,
  page,
  limit,
  totalPages: Math.ceil(total / limit),
});
