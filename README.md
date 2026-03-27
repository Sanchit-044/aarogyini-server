# Menstrual Health Monitoring – Backend API

Node.js + Express + TypeScript backend with MongoDB and Redis, fully Dockerised.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Node.js 20 (Alpine) |
| Framework | Express.js + TypeScript |
| Database | MongoDB 7 (Mongoose ODM) |
| Cache / Sessions | Redis 7 |
| Auth | JWT (access + refresh tokens) |
| Containerisation | Docker + Docker Compose |

---

## Quick Start

### 1. Clone & configure

```bash
cp .env.example .env
# Edit .env – set JWT_SECRET, JWT_REFRESH_SECRET, SESSION_SECRET at minimum
```

### 2. Run with Docker

```bash
docker compose up --build
```

Three services start:
- **app** → `http://localhost:5000`
- **mongo** → `localhost:27017`
- **redis** → `localhost:6379`

### 3. Development (local, no Docker)

```bash
npm install
npm run dev
```

---

## Project Structure

```
src/
├── config/
│   ├── env.ts            # Environment variable loader
│   ├── database.ts       # MongoDB connection
│   └── redis.ts          # Redis connection + cache helpers
├── controllers/          # Request handlers (thin layer)
│   ├── auth.controller.ts
│   ├── cycle.controller.ts
│   ├── symptom.controller.ts
│   ├── community.controller.ts
│   └── notification.controller.ts
├── middleware/
│   ├── auth.ts           # JWT protect, role guard, email-verified guard
│   ├── errorHandler.ts   # Global error handler + 404
│   └── validate.ts       # express-validator result handler
├── models/               # Mongoose schemas
│   ├── User.ts
│   ├── Cycle.ts
│   ├── Symptom.ts
│   ├── HealthAnalysis.ts
│   ├── CommunityPost.ts
│   └── Notification.ts
├── routes/
│   ├── index.ts          # Master router
│   ├── auth.routes.ts
│   ├── cycle.routes.ts
│   ├── symptom.routes.ts
│   ├── community.routes.ts
│   └── notification.routes.ts
├── services/             # Business logic
│   ├── auth.service.ts
│   ├── cycle.service.ts
│   ├── symptom.service.ts
│   ├── community.service.ts
│   └── notification.service.ts
├── types/
│   └── index.ts          # All TypeScript types, interfaces, enums
├── utils/
│   ├── AppError.ts       # Custom error classes
│   ├── email.ts          # Nodemailer helpers
│   ├── jwt.ts            # Token generation/verification
│   ├── logger.ts         # Winston logger
│   └── response.ts       # Standardised API response helpers
├── app.ts                # Express app factory
└── server.ts             # Entry point + graceful shutdown
```

---

## API Reference

Base URL: `http://localhost:5000/api`

All responses follow:
```json
{
  "success": true | false,
  "message": "...",
  "data": { ... },
  "meta": { "page": 1, "limit": 20, "total": 100, "totalPages": 5 }
}
```

---

### Auth  `/api/auth`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | ✗ | Register new user |
| POST | `/login` | ✗ | Login |
| POST | `/refresh-token` | ✗ | Refresh access token |
| POST | `/logout` | ✓ | Logout (blacklists token) |
| GET | `/verify-email/:token` | ✗ | Verify email address |
| POST | `/forgot-password` | ✗ | Send password reset email |
| POST | `/reset-password/:token` | ✗ | Reset password |
| GET | `/me` | ✓ | Get current user profile |

**Register body:**
```json
{ "email": "user@example.com", "password": "Min8chars!", "username": "jane" }
```

**Login response:**
```json
{
  "data": {
    "user": { "_id": "...", "email": "...", "username": "...", "role": "user" },
    "accessToken": "eyJ...",
    "refreshToken": "eyJ..."
  }
}
```

---

### Cycles  `/api/cycles`  🔒 (verified users)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Log new cycle (closes active cycle automatically) |
| GET | `/` | Get cycle history (paginated) |
| GET | `/active` | Get current active cycle |
| GET | `/prediction` | Predict next period & ovulation |
| PATCH | `/:id` | Update a cycle (add end date, notes, flow) |

**Log cycle body:**
```json
{
  "startDate": "2024-01-15T00:00:00.000Z",
  "flowIntensity": ["medium"],
  "notes": "Started in the morning"
}
```

**Prediction response:**
```json
{
  "data": {
    "nextPeriod": "2024-02-12T00:00:00.000Z",
    "nextOvulation": "2024-01-29T00:00:00.000Z",
    "avgCycleLength": 28
  }
}
```

---

### Symptoms  `/api/symptoms`  🔒 (verified users)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Log a symptom entry |
| GET | `/` | Get symptoms (filter by date range, category) |
| DELETE | `/:id` | Delete a symptom |
| GET | `/analysis/run` | Run AI health analysis on last 30 days |
| GET | `/analysis/history` | Get past health analyses |

**Log symptom body:**
```json
{
  "category": "pain",
  "symptoms": ["cramps", "lower_back_pain"],
  "severity": 7,
  "date": "2024-01-15T08:00:00.000Z",
  "notes": "Started after waking up"
}
```

**Symptom categories:** `pain` | `mood` | `physical` | `infection` | `hormonal`

**Available symptoms (examples):**
- Pain: `cramps`, `lower_back_pain`, `headache`, `breast_tenderness`
- Mood: `mood_swings`, `anxiety`, `irritability`
- Physical: `fatigue`, `bloating`, `nausea`, `heavy_bleeding`
- Infection: `itching`, `thick_white_discharge`, `unusual_discharge`, `burning_urination`, `frequent_urination`
- Hormonal: `acne`, `excessive_hair_growth`, `weight_gain`, `irregular_periods`

**Health analysis response:**
```json
{
  "data": {
    "detectedConditions": [
      {
        "type": "dysmenorrhea",
        "confidence": 0.85,
        "symptoms": ["cramps", "lower_back_pain"],
        "recommendation": "Severe period pain may need medical evaluation..."
      }
    ],
    "overallRisk": "medium",
    "requiresDoctorConsult": true
  }
}
```

**Detectable conditions:**
- Disorders: `dysmenorrhea`, `menorrhagia`, `amenorrhea`, `pcos`, `pcod`, `pms`, `endometriosis`
- Infections: `yeast_infection`, `bacterial_vaginosis`, `uti`

---

### Community  `/api/community`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | ✗ | List posts (filter by tag, search) |
| GET | `/:id` | ✗ | Get single post + replies |
| POST | `/` | 🔒 | Create post (anonymous by default) |
| POST | `/:id/replies` | 🔒 | Add reply to post |
| POST | `/:id/upvote` | 🔒 | Toggle upvote on post |
| POST | `/:id/flag` | 🔒 | Flag post for review |
| DELETE | `/:id` | 🔒 | Delete own post (admin deletes any) |
| PATCH | `/:id/replies/:replyId/verify` | 🔒 Doctor | Mark reply as doctor-verified |
| PATCH | `/:id/moderate` | 🔒 Admin | Change post status |

**Create post body:**
```json
{
  "title": "Is irregular period normal?",
  "content": "I have been having irregular cycles for 3 months...",
  "tags": ["cycle", "pcos"],
  "isAnonymous": true
}
```

**Query params for GET /:** `?tag=pcos&search=irregular&page=1&limit=20`

---

### Notifications  `/api/notifications`  🔒

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get notifications (paginated) |
| PATCH | `/:id/read` | Mark single notification as read |
| PATCH | `/read-all` | Mark all as read |

**Notification types:** `cycle_reminder` | `ovulation_alert` | `health_alert` | `doctor_response` | `community_reply`

---

## User Roles

| Role | Permissions |
|---|---|
| `user` | Standard access to all personal features |
| `doctor` | Can verify community replies as medically accurate |
| `admin` | Full access: moderation, role management |

---

## Security Features

- JWT access tokens (7d) + refresh tokens (30d) with rotation
- Token blacklisting on logout via Redis
- Bcrypt password hashing (salt rounds: 12)
- Helmet security headers
- CORS whitelist
- MongoDB operator injection sanitisation
- Rate limiting: 100 req/15min globally, 20 req/15min on auth routes
- Request body size limit: 10kb

---

## Environment Variables

See `.env.example` for full list. Required in production:

```
JWT_SECRET=<32+ random chars>
JWT_REFRESH_SECRET=<32+ random chars>
SESSION_SECRET=<32+ random chars>
MONGO_URI=mongodb://mongo:27017/menstrual_health_db
```
