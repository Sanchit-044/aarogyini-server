import { Notification } from '../models/Notification';
import { INotification } from '../types';
import { NotFoundError } from '../utils/AppError';

export class NotificationService {
  async getNotifications(
    userId: string,
    page = 1,
    limit = 20
  ): Promise<{ notifications: INotification[]; total: number; unreadCount: number }> {
    const skip = (page - 1) * limit;
    const [notifications, total, unreadCount] = await Promise.all([
      Notification.find({ userId }).sort({ createdAt: -1 }).skip(skip).limit(limit),
      Notification.countDocuments({ userId }),
      Notification.countDocuments({ userId, isRead: false }),
    ]);
    return { notifications, total, unreadCount };
  }

  async markRead(userId: string, notificationId: string): Promise<void> {
    const n = await Notification.findOneAndUpdate(
      { _id: notificationId, userId },
      { isRead: true }
    );
    if (!n) throw new NotFoundError('Notification');
  }

  async markAllRead(userId: string): Promise<void> {
    await Notification.updateMany({ userId, isRead: false }, { isRead: true });
  }
}

export const notificationService = new NotificationService();
