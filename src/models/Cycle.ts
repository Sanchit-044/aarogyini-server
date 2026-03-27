import mongoose, { Schema } from 'mongoose';
import { ICycle, CyclePhase, FlowIntensity } from '../types';

const CycleSchema = new Schema<ICycle>(
  {
    userId: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    startDate: { type: Date, required: true },
    endDate: { type: Date },
    cycleLength: { type: Number, min: 15, max: 60 },
    periodLength: { type: Number, min: 1, max: 15 },
    flowIntensity: [{ type: String, enum: Object.values(FlowIntensity) }],
    phase: { type: String, enum: Object.values(CyclePhase), default: CyclePhase.MENSTRUAL },
    notes: { type: String, maxlength: 1000 },
    isActive: { type: Boolean, default: true },
  },
  { timestamps: true }
);

CycleSchema.index({ userId: 1, startDate: -1 });

export const Cycle = mongoose.model<ICycle>('Cycle', CycleSchema);
