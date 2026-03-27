import { Router, Request, Response } from 'express';
import authRoutes from './auth.routes';
import cycleRoutes from './cycle.routes';
import symptomRoutes from './symptom.routes';
import communityRoutes from './community.routes';
import notificationRoutes from './notification.routes';

const router = Router();

router.get('/health', (_req: Request, res: Response) => {
  res.json({ success: true, message: 'API is healthy', timestamp: new Date().toISOString() });
});

router.use('/auth', authRoutes);
router.use('/cycles', cycleRoutes);
router.use('/symptoms', symptomRoutes);
router.use('/community', communityRoutes);
router.use('/notifications', notificationRoutes);

export default router;
