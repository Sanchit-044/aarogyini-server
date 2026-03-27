import mongoose, { Schema } from "mongoose";
import bcrypt from "bcryptjs";
import { IUser, UserRole } from "../types";

const UserSchema = new Schema<IUser>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },
    password: { type: String, required: true, minlength: 8, select: false },
    username: { type: String, required: true, trim: true, maxlength: 50 },
    role: {
      type: String,
      enum: Object.values(UserRole),
      default: UserRole.USER,
    },
    profile: {
      age: { type: Number, min: 10, max: 100 },
      averageCycleLength: { type: Number, default: 28, min: 21, max: 45 },
      averagePeriodLength: { type: Number, default: 5, min: 2, max: 10 },
    },
    isVerified: { type: Boolean, default: false },
    isActive: { type: Boolean, default: true },
    refreshToken: { type: String, select: false },
    passwordResetToken: { type: String, select: false },
    passwordResetExpires: { type: Date, select: false },
    emailVerificationToken: { type: String, select: false },
  },
  { timestamps: true },
);

UserSchema.pre("save", async function (next) {
  if (!this.isModified("password")) return next();
  this.password = await bcrypt.hash(this.password, 12);
  next();
});

UserSchema.methods.comparePassword = async function (
  candidatePassword: string,
): Promise<boolean> {
  return bcrypt.compare(candidatePassword, this.get("password"));
};

UserSchema.set("toJSON", {
  transform: (_doc, ret) => {
    const { password, refreshToken, __v, ...safeUser } = ret;
    return safeUser;
  },
});

export const User = mongoose.model<IUser>("User", UserSchema);
