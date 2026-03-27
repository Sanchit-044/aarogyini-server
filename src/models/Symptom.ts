import mongoose, { Schema } from 'mongoose';
import { ISymptom, SymptomCategory } from '../types';

const SymptomSchema = new Schema<ISymptom>(
  {
    userId: { type: Schema.Types.ObjectId, ref: 'User', required: true, index: true },
    cycleId: { type: Schema.Types.ObjectId, ref: 'Cycle' },
    date: { type: Date, required: true, default: Date.now },
    category: { type: String, enum: Object.values(SymptomCategory), required: true },
    symptoms: [{ type: String, required: true }],
    severity: { type: Number, min: 1, max: 10, required: true },
    notes: { type: String, maxlength: 500 },
  },
  { timestamps: true }
);

SymptomSchema.index({ userId: 1, date: -1 });

export const Symptom = mongoose.model<ISymptom>('Symptom', SymptomSchema);
