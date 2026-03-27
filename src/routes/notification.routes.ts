import { Router } from 'express';
import * as notifCtrl from '../controllers/notification.controller';
import { protect } from '../middleware/auth';

const router = Router();

router.use(protect);

router.get('/', notifCtrl.getNotifications);
router.patch('/read-all', notifCtrl.markAllRead);
router.patch('/:id/read', notifCtrl.markRead);

export default router;
