import nodemailer from 'nodemailer';
import { config } from '../config/env';
import { logger } from './logger';

const transporter = nodemailer.createTransport({
  host: config.email.host,
  port: config.email.port,
  secure: config.email.port === 465,
  auth: { user: config.email.user, pass: config.email.pass },
});

interface EmailOptions {
  to: string;
  subject: string;
  html: string;
}

export const sendEmail = async (options: EmailOptions): Promise<void> => {
  try {
    await transporter.sendMail({ from: config.email.from, ...options });
    logger.info(`Email sent to ${options.to}`);
  } catch (error) {
    logger.error(`Email error: ${(error as Error).message}`);
    throw error;
  }
};

export const sendVerificationEmail = async (to: string, token: string): Promise<void> => {
  const url = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/verify-email?token=${token}`;
  await sendEmail({
    to,
    subject: 'Verify Your Email – Menstrual Health',
    html: `<p>Click <a href="${url}">here</a> to verify your email. Link expires in 24 hours.</p>`,
  });
};

export const sendPasswordResetEmail = async (to: string, token: string): Promise<void> => {
  const url = `${process.env.FRONTEND_URL || 'http://localhost:3000'}/reset-password?token=${token}`;
  await sendEmail({
    to,
    subject: 'Password Reset – Menstrual Health',
    html: `<p>Click <a href="${url}">here</a> to reset your password. Link expires in 1 hour.</p>`,
  });
};
