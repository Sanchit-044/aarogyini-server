import { Response, NextFunction } from 'express';
import { notificationService } from '../services/notification.service';
import { AuthRequest } from '../types';
import { sendSuccess, getPaginationMeta } from '../utils/response';

export const getNotifications = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const result = await notificationService.getNotifications(req.user!._id.toString(), page, limit);
    sendSuccess(res, result, 'Notifications fetched', 200, getPaginationMeta(result.total, page, limit));
  } catch (err) { next(err); }
};

export const markRead = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    await notificationService.markRead(req.user!._id.toString(), req.params.id);
    sendSuccess(res, null, 'Notification marked as read');
  } catch (err) { next(err); }
};

export const markAllRead = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    await notificationService.markAllRead(req.user!._id.toString());
    sendSuccess(res, null, 'All notifications marked as read');
  } catch (err) { next(err); }
};
