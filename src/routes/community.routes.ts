import { Router } from 'express';
import { body } from 'express-validator';
import * as communityCtrl from '../controllers/community.controller';
import { protect, restrictTo } from '../middleware/auth';
import { validate } from '../middleware/validate';
import { UserRole, PostStatus } from '../types';

const router = Router();

// Public routes
router.get('/', communityCtrl.getPosts);
router.get('/:id', communityCtrl.getPost);

// Auth required
router.use(protect);

router.post(
  '/',
  [
    body('title').trim().notEmpty().isLength({ max: 200 }).withMessage('Title required (max 200 chars)'),
    body('content').trim().notEmpty().isLength({ max: 5000 }).withMessage('Content required (max 5000 chars)'),
    body('tags').optional().isArray(),
    body('isAnonymous').optional().isBoolean(),
  ],
  validate,
  communityCtrl.createPost
);

router.post(
  '/:id/replies',
  [
    body('content').trim().notEmpty().isLength({ max: 2000 }).withMessage('Reply content required'),
    body('isAnonymous').optional().isBoolean(),
  ],
  validate,
  communityCtrl.addReply
);

router.post('/:id/upvote', communityCtrl.upvotePost);
router.post('/:id/flag', communityCtrl.flagPost);
router.delete('/:id', communityCtrl.deletePost);

// Doctor only
router.patch(
  '/:id/replies/:replyId/verify',
  restrictTo(UserRole.DOCTOR, UserRole.ADMIN),
  communityCtrl.verifyReply
);

// Admin only
router.patch(
  '/:id/moderate',
  restrictTo(UserRole.ADMIN),
  [body('status').isIn(Object.values(PostStatus)).withMessage('Invalid status')],
  validate,
  communityCtrl.moderatePost
);

export default router;
