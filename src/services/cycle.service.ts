import { Types } from 'mongoose';
import { Cycle } from '../models/Cycle';
import { ICycle, CyclePhase, FlowIntensity } from '../types';
import { AppError, NotFoundError } from '../utils/AppError';
import { cacheGet, cacheSet, cacheDel } from '../config/redis';
import { Notification } from '../models/Notification';
import { NotificationType } from '../types';

const CACHE_TTL = 300; // 5 min

export class CycleService {
  private cacheKey(userId: string) {
    return `cycles:${userId}`;
  }

  async logCycle(
    userId: string,
    data: { startDate: Date; flowIntensity?: FlowIntensity[]; notes?: string }
  ): Promise<ICycle> {
    // Close any existing active cycle
    await Cycle.findOneAndUpdate(
      { userId, isActive: true },
      { isActive: false, endDate: data.startDate }
    );

    const cycle = await Cycle.create({ userId, ...data, phase: CyclePhase.MENSTRUAL, isActive: true });
    await cacheDel(this.cacheKey(userId));

    // Schedule ovulation notification (approx. day 14)
    const ovulationDate = new Date(data.startDate);
    ovulationDate.setDate(ovulationDate.getDate() + 14);
    await Notification.create({
      userId,
      type: NotificationType.OVULATION_ALERT,
      title: 'Ovulation Window Approaching',
      message: `Your estimated ovulation date is ${ovulationDate.toDateString()}. Track your symptoms for accuracy.`,
      metadata: { cycleId: cycle._id, estimatedOvulation: ovulationDate },
    });

    return cycle;
  }

  async updateCycle(userId: string, cycleId: string, data: Partial<ICycle>): Promise<ICycle> {
    const cycle = await Cycle.findOneAndUpdate({ _id: cycleId, userId }, data, { new: true, runValidators: true });
    if (!cycle) throw new NotFoundError('Cycle');
    await cacheDel(this.cacheKey(userId));

    // If endDate added, compute lengths
    if (data.endDate && cycle.startDate) {
      const periodMs = new Date(data.endDate).getTime() - cycle.startDate.getTime();
      cycle.periodLength = Math.round(periodMs / 86400000);
      await cycle.save();
    }

    return cycle;
  }

  async getCycles(userId: string, page = 1, limit = 10): Promise<{ cycles: ICycle[]; total: number }> {
    const cacheKey = `${this.cacheKey(userId)}:p${page}:l${limit}`;
    const cached = await cacheGet<{ cycles: ICycle[]; total: number }>(cacheKey);
    if (cached) return cached;

    const skip = (page - 1) * limit;
    const [cycles, total] = await Promise.all([
      Cycle.find({ userId }).sort({ startDate: -1 }).skip(skip).limit(limit),
      Cycle.countDocuments({ userId }),
    ]);

    const result = { cycles, total };
    await cacheSet(cacheKey, result, CACHE_TTL);
    return result;
  }

  async getActiveCycle(userId: string): Promise<ICycle | null> {
    return Cycle.findOne({ userId, isActive: true });
  }

  async getCyclePrediction(userId: string): Promise<{ nextPeriod: Date; nextOvulation: Date; avgCycleLength: number }> {
    const recentCycles = await Cycle.find({ userId, endDate: { $exists: true } })
      .sort({ startDate: -1 })
      .limit(6);

    const avgLength =
      recentCycles.length >= 2
        ? Math.round(
            recentCycles.slice(0, -1).reduce((sum, c, i) => {
              const diff =
                (recentCycles[i].startDate.getTime() - recentCycles[i + 1].startDate.getTime()) /
                86400000;
              return sum + diff;
            }, 0) / (recentCycles.length - 1)
          )
        : 28;

    const lastCycle = recentCycles[0];
    const baseDate = lastCycle ? new Date(lastCycle.startDate) : new Date();
    const nextPeriod = new Date(baseDate);
    nextPeriod.setDate(nextPeriod.getDate() + avgLength);

    const nextOvulation = new Date(nextPeriod);
    nextOvulation.setDate(nextOvulation.getDate() - 14);

    return { nextPeriod, nextOvulation, avgCycleLength: avgLength };
  }
}

export const cycleService = new CycleService();
