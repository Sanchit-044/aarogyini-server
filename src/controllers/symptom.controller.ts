import { Response, NextFunction } from 'express';
import { symptomService } from '../services/symptom.service';
import { AuthRequest, SymptomCategory } from '../types';
import { sendSuccess, sendCreated, getPaginationMeta } from '../utils/response';

export const logSymptom = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const symptom = await symptomService.logSymptom(req.user!._id.toString(), req.body);
    sendCreated(res, symptom, 'Symptom logged');
  } catch (err) { next(err); }
};

export const getSymptoms = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const filters = {
      startDate: req.query.startDate ? new Date(req.query.startDate as string) : undefined,
      endDate: req.query.endDate ? new Date(req.query.endDate as string) : undefined,
      category: req.query.category as SymptomCategory | undefined,
    };
    const { symptoms, total } = await symptomService.getSymptoms(req.user!._id.toString(), filters, page, limit);
    sendSuccess(res, symptoms, 'Symptoms fetched', 200, getPaginationMeta(total, page, limit));
  } catch (err) { next(err); }
};

export const deleteSymptom = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    await symptomService.deleteSymptom(req.user!._id.toString(), req.params.id);
    sendSuccess(res, null, 'Symptom deleted');
  } catch (err) { next(err); }
};

export const analyzeHealth = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const analysis = await symptomService.analyzeHealth(req.user!._id.toString());
    sendSuccess(res, analysis, 'Health analysis complete');
  } catch (err) { next(err); }
};

export const getHealthHistory = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const history = await symptomService.getHealthHistory(req.user!._id.toString());
    sendSuccess(res, history, 'Health history fetched');
  } catch (err) { next(err); }
};
