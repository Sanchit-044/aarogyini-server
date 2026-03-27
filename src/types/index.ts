import { Request } from 'express';
import { Document, Types } from 'mongoose';

// ─── Enums ────────────────────────────────────────────────────────────────────

export enum UserRole {
  USER = 'user',
  DOCTOR = 'doctor',
  ADMIN = 'admin',
}

export enum CyclePhase {
  MENSTRUAL = 'menstrual',
  FOLLICULAR = 'follicular',
  OVULATION = 'ovulation',
  LUTEAL = 'luteal',
}

export enum FlowIntensity {
  SPOTTING = 'spotting',
  LIGHT = 'light',
  MEDIUM = 'medium',
  HEAVY = 'heavy',
  VERY_HEAVY = 'very_heavy',
}

export enum SymptomCategory {
  PAIN = 'pain',
  MOOD = 'mood',
  PHYSICAL = 'physical',
  INFECTION = 'infection',
  HORMONAL = 'hormonal',
}

export enum DisorderType {
  DYSMENORRHEA = 'dysmenorrhea',
  MENORRHAGIA = 'menorrhagia',
  AMENORRHEA = 'amenorrhea',
  PCOS = 'pcos',
  PCOD = 'pcod',
  PMS = 'pms',
  ENDOMETRIOSIS = 'endometriosis',
}

export enum InfectionType {
  YEAST_INFECTION = 'yeast_infection',
  BACTERIAL_VAGINOSIS = 'bacterial_vaginosis',
  UTI = 'uti',
}

export enum PostStatus {
  ACTIVE = 'active',
  FLAGGED = 'flagged',
  REMOVED = 'removed',
}

export enum NotificationType {
  CYCLE_REMINDER = 'cycle_reminder',
  OVULATION_ALERT = 'ovulation_alert',
  HEALTH_ALERT = 'health_alert',
  DOCTOR_RESPONSE = 'doctor_response',
  COMMUNITY_REPLY = 'community_reply',
}

// ─── User Types ───────────────────────────────────────────────────────────────

export interface IUser extends Document {
  _id: Types.ObjectId;
  email: string;
  password: string;
  username: string;
  role: UserRole;
  profile: {
    age?: number;
    averageCycleLength?: number;
    averagePeriodLength?: number;
  };
  isVerified: boolean;
  isActive: boolean;
  refreshToken?: string;
  passwordResetToken?: string;
  passwordResetExpires?: Date;
  emailVerificationToken?: string;
  createdAt: Date;
  updatedAt: Date;
  comparePassword(candidatePassword: string): Promise<boolean>;
}

// ─── Cycle Types ──────────────────────────────────────────────────────────────

export interface ICycle extends Document {
  _id: Types.ObjectId;
  userId: Types.ObjectId;
  startDate: Date;
  endDate?: Date;
  cycleLength?: number;
  periodLength?: number;
  flowIntensity: FlowIntensity[];
  phase: CyclePhase;
  notes?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// ─── Symptom Types ────────────────────────────────────────────────────────────

export interface ISymptom extends Document {
  _id: Types.ObjectId;
  userId: Types.ObjectId;
  cycleId?: Types.ObjectId;
  date: Date;
  category: SymptomCategory;
  symptoms: string[];
  severity: number; // 1-10
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

// ─── Health Analysis Types ────────────────────────────────────────────────────

export interface IHealthAnalysis extends Document {
  _id: Types.ObjectId;
  userId: Types.ObjectId;
  analysisDate: Date;
  detectedConditions: Array<{
    type: DisorderType | InfectionType;
    confidence: number;
    symptoms: string[];
    recommendation: string;
  }>;
  overallRisk: 'low' | 'medium' | 'high';
  requiresDoctorConsult: boolean;
  createdAt: Date;
}

// ─── Community Types ──────────────────────────────────────────────────────────

export interface ICommunityPost extends Document {
  _id: Types.ObjectId;
  authorId: Types.ObjectId;
  isAnonymous: boolean;
  title: string;
  content: string;
  tags: string[];
  status: PostStatus;
  upvotes: Types.ObjectId[];
  views: number;
  replies: IReply[];
  createdAt: Date;
  updatedAt: Date;
}

export interface IReply {
  _id: Types.ObjectId;
  authorId: Types.ObjectId;
  isAnonymous: boolean;
  content: string;
  isVerifiedByDoctor: boolean;
  verifiedBy?: Types.ObjectId;
  verifiedAt?: Date;
  upvotes: Types.ObjectId[];
  isFlagged: boolean;
  createdAt: Date;
}

// ─── Notification Types ───────────────────────────────────────────────────────

export interface INotification extends Document {
  _id: Types.ObjectId;
  userId: Types.ObjectId;
  type: NotificationType;
  title: string;
  message: string;
  isRead: boolean;
  metadata?: Record<string, unknown>;
  createdAt: Date;
}

// ─── Request Extensions ───────────────────────────────────────────────────────

export interface AuthRequest extends Request {
  user?: IUser;
}

// ─── API Response Types ───────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  errors?: string[];
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    totalPages?: number;
  };
}

export interface PaginationQuery {
  page?: string;
  limit?: string;
  sort?: string;
  order?: 'asc' | 'desc';
}
