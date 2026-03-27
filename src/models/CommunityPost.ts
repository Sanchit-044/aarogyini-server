import mongoose, { Schema } from 'mongoose';
import { ICommunityPost, PostStatus } from '../types';

const ReplySchema = new Schema(
  {
    authorId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
    isAnonymous: { type: Boolean, default: true },
    content: { type: String, required: true, maxlength: 2000 },
    isVerifiedByDoctor: { type: Boolean, default: false },
    verifiedBy: { type: Schema.Types.ObjectId, ref: 'User' },
    verifiedAt: { type: Date },
    upvotes: [{ type: Schema.Types.ObjectId, ref: 'User' }],
    isFlagged: { type: Boolean, default: false },
  },
  { timestamps: true }
);

const CommunityPostSchema = new Schema<ICommunityPost>(
  {
    authorId: { type: Schema.Types.ObjectId, ref: 'User', required: true },
    isAnonymous: { type: Boolean, default: true },
    title: { type: String, required: true, maxlength: 200 },
    content: { type: String, required: true, maxlength: 5000 },
    tags: [{ type: String, lowercase: true, trim: true }],
    status: { type: String, enum: Object.values(PostStatus), default: PostStatus.ACTIVE },
    upvotes: [{ type: Schema.Types.ObjectId, ref: 'User' }],
    views: { type: Number, default: 0 },
    replies: [ReplySchema],
  },
  { timestamps: true }
);

CommunityPostSchema.index({ createdAt: -1 });
CommunityPostSchema.index({ tags: 1 });
CommunityPostSchema.index({ status: 1 });

export const CommunityPost = mongoose.model<ICommunityPost>('CommunityPost', CommunityPostSchema);
