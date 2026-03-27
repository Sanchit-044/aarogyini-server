// MongoDB initialization script
db = db.getSiblingDB('menstrual_health_db');

db.createCollection('users');
db.createCollection('cycles');
db.createCollection('symptoms');
db.createCollection('community_posts');
db.createCollection('notifications');

// Indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.cycles.createIndex({ userId: 1, startDate: -1 });
db.symptoms.createIndex({ userId: 1, date: -1 });
db.community_posts.createIndex({ createdAt: -1 });
db.community_posts.createIndex({ tags: 1 });
db.notifications.createIndex({ userId: 1, createdAt: -1 });

print('MongoDB initialized successfully');
