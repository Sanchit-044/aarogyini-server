import { Request, Response, NextFunction } from "express";
import { communityService } from "../services/community.service";
import { AuthRequest, PostStatus, UserRole } from "../types";
import { sendSuccess, sendCreated, getPaginationMeta } from "../utils/response";

export const createPost = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const post = await communityService.createPost(
      req.user!._id.toString(),
      req.body,
    );
    sendCreated(res, post, "Post created");
  } catch (err) {
    next(err);
  }
};

export const getPosts = async (
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const { posts, total } = await communityService.getPosts(
      { tag: req.query.tag as string, search: req.query.search as string },
      page,
      limit,
    );
    sendSuccess(
      res,
      posts,
      "Posts fetched",
      200,
      getPaginationMeta(total, page, limit),
    );
  } catch (err) {
    next(err);
  }
};

export const getPost = async (
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const post = await communityService.getPost(req.params.id);
    sendSuccess(res, post, "Post fetched");
  } catch (err) {
    next(err);
  }
};

export const addReply = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const { content, isAnonymous } = req.body;
    const post = await communityService.addReply(
      req.params.id,
      req.user!._id.toString(),
      content,
      isAnonymous,
    );
    sendCreated(res, post, "Reply added");
  } catch (err) {
    next(err);
  }
};

export const verifyReply = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const post = await communityService.verifyReply(
      req.params.id,
      req.params.replyId,
      req.user!._id.toString(),
    );
    sendSuccess(res, post, "Reply verified by doctor");
  } catch (err) {
    next(err);
  }
};

export const upvotePost = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const result = await communityService.upvotePost(
      req.params.id,
      req.user!._id.toString(),
    );
    sendSuccess(res, result, "Upvote toggled");
  } catch (err) {
    next(err);
  }
};

export const flagPost = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    await communityService.flagPost(req.params.id);
    sendSuccess(res, null, "Post flagged for review");
  } catch (err) {
    next(err);
  }
};

export const moderatePost = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const post = await communityService.moderatePost(
      req.params.id,
      req.body.status as PostStatus,
    );
    sendSuccess(res, post, "Post moderated");
  } catch (err) {
    next(err);
  }
};

export const deletePost = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    await communityService.deletePost(
      req.params.id,
      req.user!._id.toString(),
      req.user!.role,
    );
    sendSuccess(res, null, "Post deleted");
  } catch (err) {
    next(err);
  }
};
