import jwt from 'jsonwebtoken';
import { config } from '../config/env';
import { Types } from 'mongoose';

interface TokenPayload {
  id: string;
  role: string;
}

export const generateAccessToken = (id: Types.ObjectId, role: string): string => {
  return jwt.sign({ id: id.toString(), role }, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn as string,
  } as jwt.SignOptions);
};

export const generateRefreshToken = (id: Types.ObjectId): string => {
  return jwt.sign({ id: id.toString() }, config.jwt.refreshSecret, {
    expiresIn: config.jwt.refreshExpiresIn as string,
  } as jwt.SignOptions);
};

export const verifyAccessToken = (token: string): TokenPayload => {
  return jwt.verify(token, config.jwt.secret) as TokenPayload;
};

export const verifyRefreshToken = (token: string): TokenPayload => {
  return jwt.verify(token, config.jwt.refreshSecret) as TokenPayload;
};
