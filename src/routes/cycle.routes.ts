import { Router } from 'express';
import { body } from 'express-validator';
import * as cycleCtrl from '../controllers/cycle.controller';
import { protect, requireVerified } from '../middleware/auth';
import { validate } from '../middleware/validate';

const router = Router();

router.use(protect, requireVerified);

router.post(
  '/',
  [body('startDate').isISO8601().withMessage('Valid start date required')],
  validate,
  cycleCtrl.logCycle
);

router.get('/', cycleCtrl.getCycles);
router.get('/active', cycleCtrl.getActiveCycle);
router.get('/prediction', cycleCtrl.getCyclePrediction);
router.patch('/:id', cycleCtrl.updateCycle);

export default router;
