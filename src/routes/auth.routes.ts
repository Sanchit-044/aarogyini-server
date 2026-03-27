import { Router } from "express";
import { body } from "express-validator";
import * as authCtrl from "../controllers/auth.controller";
import { protect } from "../middleware/auth";
import { validate } from "../middleware/validate";

const router = Router();

router.post(
  "/register",
  [
    body("email")
      .isEmail()
      .normalizeEmail()
      .withMessage("Valid email required"),
    body("password")
      .isLength({ min: 8 })
      .withMessage("Password must be at least 8 characters"),
    body("username")
      .trim()
      .notEmpty()
      .isLength({ max: 50 })
      .withMessage("Username required (max 50 chars)"),
  ],
  validate,
  authCtrl.register,
);

router.post(
  "/login",
  [
    body("email").isEmail().normalizeEmail(),
    body("password").notEmpty().withMessage("Password required"),
  ],
  validate,
  authCtrl.login,
);

router.post(
  "/refresh-token",
  [body("refreshToken").notEmpty().withMessage("Refresh token required")],
  validate,
  authCtrl.refreshToken,
);

router.post("/logout", protect, authCtrl.logout);

router.get("/verify-email/:token", authCtrl.verifyEmail);

router.post(
  "/forgot-password",
  [body("email").isEmail().normalizeEmail()],
  validate,
  authCtrl.forgotPassword,
);

router.post(
  "/reset-password/:token",
  [
    body("password")
      .isLength({ min: 8 })
      .withMessage("Password must be at least 8 characters"),
  ],
  validate,
  authCtrl.resetPassword,
);

router.get("/me", protect, authCtrl.getMe);

export default router;
