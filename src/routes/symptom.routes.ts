import { Router } from 'express';
import { body } from 'express-validator';
import * as symptomCtrl from '../controllers/symptom.controller';
import { protect, requireVerified } from '../middleware/auth';
import { validate } from '../middleware/validate';
import { SymptomCategory } from '../types';

const router = Router();

router.use(protect, requireVerified);

router.post(
  '/',
  [
    body('category').isIn(Object.values(SymptomCategory)).withMessage('Invalid symptom category'),
    body('symptoms').isArray({ min: 1 }).withMessage('At least one symptom required'),
    body('severity').isInt({ min: 1, max: 10 }).withMessage('Severity must be 1–10'),
  ],
  validate,
  symptomCtrl.logSymptom
);

router.get('/', symptomCtrl.getSymptoms);
router.delete('/:id', symptomCtrl.deleteSymptom);
router.get('/analysis/run', symptomCtrl.analyzeHealth);
router.get('/analysis/history', symptomCtrl.getHealthHistory);

export default router;
