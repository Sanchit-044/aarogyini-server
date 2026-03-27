import mongoose, { Schema } from 'mongoose';
import { IHealthAnalysis, DisorderType, InfectionType } from '../types';

const HealthAnalysisSchema = new Schema<IHealthAnalysis>(
  {
    userId: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    analysisDate: { type: Date, default: Date.now },
    detectedConditions: [
      {
        type: {
          type: String,
          enum: [...Object.values(DisorderType), ...Object.values(InfectionType)],
        },
        confidence: { type: Number, min: 0, max: 1 },
        symptoms: [String],
        recommendation: String,
      },
    ],
    overallRisk: { type: String, enum: ['low', 'medium', 'high'], default: 'low' },
    requiresDoctorConsult: { type: Boolean, default: false },
  },
  { timestamps: true }
);

export const HealthAnalysis = mongoose.model<IHealthAnalysis>('HealthAnalysis', HealthAnalysisSchema);
