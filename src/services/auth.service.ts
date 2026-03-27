import crypto from "crypto";
import { User } from "../models/User";
import { IUser, UserRole } from "../types";
import {
  generateAccessToken,
  generateRefreshToken,
  verifyRefreshToken,
} from "../utils/jwt";
import { AppError, UnauthorizedError } from "../utils/AppError";
import { sendVerificationEmail, sendPasswordResetEmail } from "../utils/email";
import { getRedis } from "../config/redis";
import { config } from "../config/env";
import { logger } from "../utils/logger";

export class AuthService {
  async register(
    email: string,
    password: string,
    username: string,
  ): Promise<{ user: IUser; accessToken: string; refreshToken: string }> {
    const existing = await User.findOne({ email });
    if (existing) throw new AppError("Email already registered", 409);

    const verificationToken = crypto.randomBytes(32).toString("hex");
    const user = await User.create({
      email,
      password,
      username,
      emailVerificationToken: verificationToken,
    });

    try {
      await sendVerificationEmail(email, verificationToken);
    } catch (err) {
      logger.warn(`Could not send verification email to ${email}`);
    }

    const accessToken = generateAccessToken(user._id, user.role);
    const refreshToken = generateRefreshToken(user._id);
    user.refreshToken = refreshToken;
    await user.save({ validateBeforeSave: false });

    return { user, accessToken, refreshToken };
  }

  async login(
    email: string,
    password: string,
  ): Promise<{ user: IUser; accessToken: string; refreshToken: string }> {
    const user = await User.findOne({ email }).select(
      "+password +refreshToken",
    );
    if (!user || !(await user.comparePassword(password))) {
      throw new UnauthorizedError("Invalid email or password");
    }
    if (!user.isActive) throw new AppError("Account deactivated", 403);

    const accessToken = generateAccessToken(user._id, user.role);
    const refreshToken = generateRefreshToken(user._id);
    user.refreshToken = refreshToken;
    await user.save({ validateBeforeSave: false });

    return { user, accessToken, refreshToken };
  }

  async refreshToken(
    token: string,
  ): Promise<{ accessToken: string; refreshToken: string }> {
    const decoded = verifyRefreshToken(token);
    const user = await User.findById(decoded.id).select("+refreshToken");
    if (!user || user.refreshToken !== token)
      throw new UnauthorizedError("Invalid refresh token");

    const accessToken = generateAccessToken(user._id, user.role);
    const newRefresh = generateRefreshToken(user._id);
    user.refreshToken = newRefresh;
    await user.save({ validateBeforeSave: false });

    return { accessToken, refreshToken: newRefresh };
  }

  async logout(userId: string, accessToken: string): Promise<void> {
    await User.findByIdAndUpdate(userId, { $unset: { refreshToken: 1 } });
    // Blacklist the access token until it expires
    const redis = getRedis();
    await redis.set(`bl_${accessToken}`, "1", "EX", 7 * 24 * 3600);
  }

  async verifyEmail(token: string): Promise<void> {
    const user = await User.findOne({ emailVerificationToken: token }).select(
      "+emailVerificationToken",
    );
    if (!user) throw new AppError("Invalid or expired verification token", 400);
    user.isVerified = true;
    user.emailVerificationToken = undefined;
    await user.save({ validateBeforeSave: false });
  }

  async forgotPassword(email: string): Promise<void> {
    const user = await User.findOne({ email });
    if (!user) return; // Silently succeed to prevent user enumeration

    const resetToken = crypto.randomBytes(32).toString("hex");
    user.passwordResetToken = crypto
      .createHash("sha256")
      .update(resetToken)
      .digest("hex");
    user.passwordResetExpires = new Date(Date.now() + 3600000); // 1 hour
    await user.save({ validateBeforeSave: false });

    await sendPasswordResetEmail(email, resetToken);
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    const hashedToken = crypto.createHash("sha256").update(token).digest("hex");
    const user = await User.findOne({
      passwordResetToken: hashedToken,
      passwordResetExpires: { $gt: Date.now() },
    }).select("+passwordResetToken +passwordResetExpires");

    if (!user) throw new AppError("Invalid or expired reset token", 400);

    user.password = newPassword;
    user.passwordResetToken = undefined;
    user.passwordResetExpires = undefined;
    await user.save();
  }
}

export const authService = new AuthService();
