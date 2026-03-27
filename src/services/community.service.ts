import { Types } from 'mongoose';
import { CommunityPost } from '../models/CommunityPost';
import { ICommunityPost, PostStatus, UserRole } from '../types';
import { AppError, ForbiddenError, NotFoundError } from '../utils/AppError';
import { Notification } from '../models/Notification';
import { NotificationType } from '../types';

export class CommunityService {
  async createPost(userId: string, data: {
    title: string;
    content: string;
    tags?: string[];
    isAnonymous?: boolean;
  }): Promise<ICommunityPost> {
    return CommunityPost.create({ authorId: userId, ...data });
  }

  async getPosts(
    filters: { tag?: string; search?: string },
    page = 1,
    limit = 20
  ): Promise<{ posts: ICommunityPost[]; total: number }> {
    const query: Record<string, unknown> = { status: PostStatus.ACTIVE };
    if (filters.tag) query.tags = filters.tag;
    if (filters.search) {
      query.$or = [
        { title: { $regex: filters.search, $options: 'i' } },
        { content: { $regex: filters.search, $options: 'i' } },
      ];
    }

    const skip = (page - 1) * limit;
    const [posts, total] = await Promise.all([
      CommunityPost.find(query)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit)
        .populate({ path: 'authorId', select: 'username role', match: {} }),
      CommunityPost.countDocuments(query),
    ]);

    // Strip author identity for anonymous posts
    const sanitized = posts.map((post) => {
      const p = post.toObject() as any;
      if (p.isAnonymous) p.authorId = null;
      return p;
    });

    return { posts: sanitized, total };
  }

  async getPost(postId: string): Promise<ICommunityPost> {
    const post = await CommunityPost.findOneAndUpdate(
      { _id: postId, status: PostStatus.ACTIVE },
      { $inc: { views: 1 } },
      { new: true }
    ).populate({ path: 'authorId', select: 'username role' });

    if (!post) throw new NotFoundError('Post');
    return post;
  }

  async addReply(
    postId: string,
    userId: string,
    content: string,
    isAnonymous = true
  ): Promise<ICommunityPost> {
    const post = await CommunityPost.findById(postId);
    if (!post || post.status !== PostStatus.ACTIVE) throw new NotFoundError('Post');

    post.replies.push({
      _id: new Types.ObjectId(),
      authorId: new Types.ObjectId(userId),
      isAnonymous,
      content,
      isVerifiedByDoctor: false,
      upvotes: [],
      isFlagged: false,
      createdAt: new Date(),
    });

    await post.save();

    // Notify original author
    if (post.authorId.toString() !== userId) {
      await Notification.create({
        userId: post.authorId,
        type: NotificationType.COMMUNITY_REPLY,
        title: 'New Reply on Your Post',
        message: `Someone replied to your post: "${post.title}"`,
        metadata: { postId, replyId: post.replies[post.replies.length - 1]._id },
      });
    }

    return post;
  }

  async verifyReply(
    postId: string,
    replyId: string,
    doctorId: string
  ): Promise<ICommunityPost> {
    const post = await CommunityPost.findById(postId);
    if (!post) throw new NotFoundError('Post');

    const reply = post.replies.find((r) => r._id.toString() === replyId);
    if (!reply) throw new NotFoundError('Reply');

    reply.isVerifiedByDoctor = true;
    reply.verifiedBy = new Types.ObjectId(doctorId);
    reply.verifiedAt = new Date();
    await post.save();

    await Notification.create({
      userId: reply.authorId,
      type: NotificationType.DOCTOR_RESPONSE,
      title: 'Your Reply Was Verified by a Doctor',
      message: 'A certified doctor has verified your reply as medically accurate.',
      metadata: { postId, replyId },
    });

    return post;
  }

  async upvotePost(postId: string, userId: string): Promise<{ upvotes: number }> {
    const post = await CommunityPost.findById(postId);
    if (!post) throw new NotFoundError('Post');

    const uid = new Types.ObjectId(userId);
    const idx = post.upvotes.findIndex((id) => id.equals(uid));
    if (idx === -1) post.upvotes.push(uid);
    else post.upvotes.splice(idx, 1); // toggle
    await post.save();

    return { upvotes: post.upvotes.length };
  }

  async flagPost(postId: string): Promise<void> {
    const post = await CommunityPost.findById(postId);
    if (!post) throw new NotFoundError('Post');
    post.status = PostStatus.FLAGGED;
    await post.save();
  }

  async moderatePost(postId: string, status: PostStatus): Promise<ICommunityPost> {
    const post = await CommunityPost.findByIdAndUpdate(postId, { status }, { new: true });
    if (!post) throw new NotFoundError('Post');
    return post;
  }

  async deletePost(postId: string, userId: string, role: UserRole): Promise<void> {
    const post = await CommunityPost.findById(postId);
    if (!post) throw new NotFoundError('Post');
    if (post.authorId.toString() !== userId && role !== UserRole.ADMIN) {
      throw new ForbiddenError('Not authorized to delete this post');
    }
    await post.deleteOne();
  }
}

export const communityService = new CommunityService();
