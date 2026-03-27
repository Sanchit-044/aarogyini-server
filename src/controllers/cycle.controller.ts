import { Response, NextFunction } from 'express';
import { cycleService } from '../services/cycle.service';
import { AuthRequest } from '../types';
import { sendSuccess, sendCreated, getPaginationMeta } from '../utils/response';

export const logCycle = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const cycle = await cycleService.logCycle(req.user!._id.toString(), req.body);
    sendCreated(res, cycle, 'Cycle logged successfully');
  } catch (err) { next(err); }
};

export const updateCycle = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const cycle = await cycleService.updateCycle(req.user!._id.toString(), req.params.id, req.body);
    sendSuccess(res, cycle, 'Cycle updated');
  } catch (err) { next(err); }
};

export const getCycles = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 10;
    const { cycles, total } = await cycleService.getCycles(req.user!._id.toString(), page, limit);
    sendSuccess(res, cycles, 'Cycles fetched', 200, getPaginationMeta(total, page, limit));
  } catch (err) { next(err); }
};

export const getActiveCycle = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const cycle = await cycleService.getActiveCycle(req.user!._id.toString());
    sendSuccess(res, cycle, cycle ? 'Active cycle found' : 'No active cycle');
  } catch (err) { next(err); }
};

export const getCyclePrediction = async (req: AuthRequest, res: Response, next: NextFunction): Promise<void> => {
  try {
    const prediction = await cycleService.getCyclePrediction(req.user!._id.toString());
    sendSuccess(res, prediction, 'Cycle prediction');
  } catch (err) { next(err); }
};
