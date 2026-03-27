import { Response, NextFunction } from "express";
import { AuthRequest, UserRole } from "../types";
import { verifyAccessToken } from "../utils/jwt";
import { User } from "../models/User";
import { sendUnauthorized, sendForbidden } from "../utils/response";
import { getRedis } from "../config/redis";

export const protect = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): Promise<void> => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      sendUnauthorized(res, "No token provided");
      return;
    }

    const token = authHeader.split(" ")[1];

    // Check if token is blacklisted (logged out)
    const redis = getRedis();
    const isBlacklisted = await redis.get(`bl_${token}`);
    if (isBlacklisted) {
      sendUnauthorized(res, "Token has been invalidated");
      return;
    }

    const decoded = verifyAccessToken(token);
    const user = await User.findById(decoded.id).select("+refreshToken");

    if (!user || !user.isActive) {
      sendUnauthorized(res, "User not found or deactivated");
      return;
    }

    req.user = user;
    next();
  } catch {
    sendUnauthorized(res, "Invalid or expired token");
  }
};

export const restrictTo = (...roles: UserRole[]) => {
  return (req: AuthRequest, res: Response, next: NextFunction): void => {
    if (!req.user || !roles.includes(req.user.role)) {
      sendForbidden(res, "You do not have permission to perform this action");
      return;
    }
    next();
  };
};

export const requireVerified = (
  req: AuthRequest,
  res: Response,
  next: NextFunction,
): void => {
  if (!req.user?.isVerified) {
    sendForbidden(res, "Please verify your email first");
    return;
  }
  next();
};
