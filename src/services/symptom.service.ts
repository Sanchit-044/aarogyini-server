import { Symptom } from '../models/Symptom';
import { HealthAnalysis } from '../models/HealthAnalysis';
import { ISymptom, IHealthAnalysis, SymptomCategory, DisorderType, InfectionType } from '../types';
import { NotFoundError } from '../utils/AppError';
import { Notification } from '../models/Notification';
import { NotificationType } from '../types';

// Rule-based detection engine
const CONDITIONS: Array<{
  type: DisorderType | InfectionType;
  requiredSymptoms: string[];
  optionalSymptoms: string[];
  recommendation: string;
}> = [
  {
    type: DisorderType.DYSMENORRHEA,
    requiredSymptoms: ['cramps'],
    optionalSymptoms: ['lower_back_pain', 'nausea', 'headache'],
    recommendation: 'Severe period pain (dysmenorrhea) may need medical evaluation. Consider consulting a gynecologist if it disrupts daily life.',
  },
  {
    type: DisorderType.MENORRHAGIA,
    requiredSymptoms: ['heavy_bleeding'],
    optionalSymptoms: ['fatigue', 'dizziness'],
    recommendation: 'Heavy menstrual bleeding could indicate hormonal imbalance or uterine conditions. Please consult a doctor.',
  },
  {
    type: DisorderType.PCOS,
    requiredSymptoms: ['irregular_periods'],
    optionalSymptoms: ['acne', 'excessive_hair_growth', 'weight_gain', 'mood_swings'],
    recommendation: 'Symptoms suggest possible PCOS. A gynecologist can confirm via ultrasound and hormone tests.',
  },
  {
    type: DisorderType.PMS,
    requiredSymptoms: ['mood_swings'],
    optionalSymptoms: ['bloating', 'breast_tenderness', 'fatigue', 'cramps', 'headache'],
    recommendation: 'These symptoms are associated with PMS. Track for 2–3 cycles. Consult a doctor if symptoms are severe.',
  },
  {
    type: InfectionType.YEAST_INFECTION,
    requiredSymptoms: ['itching'],
    optionalSymptoms: ['thick_white_discharge', 'irritation', 'burning'],
    recommendation: 'Possible vaginal yeast infection. Poor hygiene or antibiotic use can trigger this. See a doctor for antifungal treatment.',
  },
  {
    type: InfectionType.BACTERIAL_VAGINOSIS,
    requiredSymptoms: ['unusual_discharge'],
    optionalSymptoms: ['unpleasant_odor', 'irritation'],
    recommendation: 'Symptoms suggest bacterial vaginosis. This requires antibiotic treatment — do not self-medicate.',
  },
  {
    type: InfectionType.UTI,
    requiredSymptoms: ['burning_urination'],
    optionalSymptoms: ['frequent_urination', 'pelvic_pain', 'urgency'],
    recommendation: 'Possible urinary tract infection. Stay hydrated and see a doctor promptly for antibiotic treatment.',
  },
];

function scoreCondition(
  userSymptoms: string[],
  required: string[],
  optional: string[]
): number {
  const hasAllRequired = required.every((s) => userSymptoms.includes(s));
  if (!hasAllRequired) return 0;
  const optionalMatches = optional.filter((s) => userSymptoms.includes(s)).length;
  const base = 0.5;
  const bonus = optional.length > 0 ? (optionalMatches / optional.length) * 0.5 : 0.5;
  return Math.min(base + bonus, 1);
}

export class SymptomService {
  async logSymptom(userId: string, data: {
    cycleId?: string;
    date?: Date;
    category: SymptomCategory;
    symptoms: string[];
    severity: number;
    notes?: string;
  }): Promise<ISymptom> {
    const symptom = await Symptom.create({ userId, ...data });
    return symptom;
  }

  async getSymptoms(
    userId: string,
    filters: { startDate?: Date; endDate?: Date; category?: SymptomCategory },
    page = 1,
    limit = 20
  ): Promise<{ symptoms: ISymptom[]; total: number }> {
    const query: Record<string, unknown> = { userId };
    if (filters.startDate || filters.endDate) {
      query.date = {};
      if (filters.startDate) (query.date as any).$gte = filters.startDate;
      if (filters.endDate) (query.date as any).$lte = filters.endDate;
    }
    if (filters.category) query.category = filters.category;

    const skip = (page - 1) * limit;
    const [symptoms, total] = await Promise.all([
      Symptom.find(query).sort({ date: -1 }).skip(skip).limit(limit),
      Symptom.countDocuments(query),
    ]);
    return { symptoms, total };
  }

  async deleteSymptom(userId: string, symptomId: string): Promise<void> {
    const s = await Symptom.findOneAndDelete({ _id: symptomId, userId });
    if (!s) throw new NotFoundError('Symptom');
  }

  async analyzeHealth(userId: string): Promise<IHealthAnalysis> {
    // Gather symptoms from last 30 days
    const since = new Date();
    since.setDate(since.getDate() - 30);
    const recent = await Symptom.find({ userId, date: { $gte: since } });

    const allSymptoms = [...new Set(recent.flatMap((s) => s.symptoms))];

    const detectedConditions = CONDITIONS.map((cond) => {
      const confidence = scoreCondition(allSymptoms, cond.requiredSymptoms, cond.optionalSymptoms);
      return confidence > 0
        ? {
            type: cond.type,
            confidence,
            symptoms: [...cond.requiredSymptoms, ...cond.optionalSymptoms].filter((s) =>
              allSymptoms.includes(s)
            ),
            recommendation: cond.recommendation,
          }
        : null;
    }).filter(Boolean) as IHealthAnalysis['detectedConditions'];

    const maxConfidence = detectedConditions.reduce((m, c) => Math.max(m, c.confidence), 0);
    const overallRisk: 'low' | 'medium' | 'high' =
      maxConfidence >= 0.8 ? 'high' : maxConfidence >= 0.5 ? 'medium' : 'low';
    const requiresDoctorConsult = overallRisk !== 'low';

    const analysis = await HealthAnalysis.create({
      userId,
      detectedConditions,
      overallRisk,
      requiresDoctorConsult,
    });

    if (requiresDoctorConsult) {
      await Notification.create({
        userId,
        type: NotificationType.HEALTH_ALERT,
        title: 'Health Alert – Please Consult a Doctor',
        message: `Based on your recent symptoms, we recommend consulting a certified gynecologist. Conditions detected: ${detectedConditions.map((c) => c.type).join(', ')}.`,
        metadata: { analysisId: analysis._id, risk: overallRisk },
      });
    }

    return analysis;
  }

  async getHealthHistory(userId: string, limit = 5): Promise<IHealthAnalysis[]> {
    return HealthAnalysis.find({ userId }).sort({ analysisDate: -1 }).limit(limit);
  }
}

export const symptomService = new SymptomService();
