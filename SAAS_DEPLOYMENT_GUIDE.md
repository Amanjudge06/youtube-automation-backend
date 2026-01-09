# 🚀 SaaS Transformation Complete - Deployment Guide

## 📋 Overview
YouTube Automation Platform has been transformed into a full-featured SaaS application with:
- ✅ Multi-tenant architecture with user isolation
- ✅ JWT-based authentication via Supabase
- ✅ Per-user API key management
- ✅ Usage tracking and rate limiting
- ✅ Video history and analytics per user
- ✅ Secure RLS policies for all tables

## 🗄️ Database Setup (CRITICAL - DO THIS FIRST)

### Step 1: Run the Complete SaaS Schema

1. **Open Supabase SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/YOUR_PROJECT_ID/sql/new
   
2. **Execute the SaaS Schema:**
   - Open file: `supabase_saas_schema.sql`
   - Copy ALL contents (450+ lines)
   - Paste into SQL Editor
   - Click "Run" or press Ctrl+Enter

3. **Verify Tables Created:**
   ```sql
   -- Run this query to verify:
   SELECT tablename FROM pg_tables 
   WHERE schemaname = 'public' 
   ORDER BY tablename;
   ```
   
   Expected tables:
   - ✅ user_settings
   - ✅ schedules
   - ✅ automation_status
   - ✅ video_history
   - ✅ user_usage
   - ✅ user_profiles

4. **Enable Supabase Authentication:**
   - Go to: Authentication → Settings
   - Enable Email provider
   - Configure email templates (optional)
   - Copy JWT Secret for .env file

## 🔐 Environment Configuration

### Step 2: Update Environment Variables

**Add to your `.env` file:**

```env
# CRITICAL: Add JWT Secret from Supabase
SUPABASE_JWT_SECRET=your-jwt-secret-from-dashboard

# Existing variables (keep these)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# API Keys (these become defaults - users can override in UI)
SERP_API_KEY=your-serp-api-key
OPENAI_API_KEY=your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
PEXELS_API_KEY=your-pexels-api-key
```

**Where to find JWT Secret:**
1. Supabase Dashboard
2. Settings → API
3. Under "JWT Secret" - click "Reveal" and copy

## 📦 Backend Dependencies

### Step 3: Install New Python Packages

```bash
cd "/Users/aman/Documents/YouTube Automation"
pip install python-jose[cryptography] passlib[bcrypt]
```

**New dependencies added to requirements.txt:**
- `python-jose[cryptography]>=3.3.0` - JWT token validation
- `passlib[bcrypt]>=1.7.4` - Password hashing (backup)

## 🎨 Frontend Setup

### Step 4: Install Frontend Dependencies (Already Done)

```bash
cd frontend
npm install
# react-router-dom is already in package.json
```

### New Frontend Components Created:
- `contexts/AuthContext.js` - Authentication state management
- `components/Login.js` - Login page
- `components/Signup.js` - Registration page
- `components/ProtectedRoute.js` - Route protection HOC
- `components/MainApp.js` - Main application with auth

### Updated Files:
- `App.js` - Now handles routing (Login/Signup/MainApp)
- All components now receive auth token in requests

## 🚢 Deployment

### Step 5: Deploy to Cloud Run

```bash
# Commit all changes
git add .
git commit -m "Transform to full SaaS with authentication and multi-tenancy"
git push

# Deploy to Cloud Run
gcloud run deploy snip-z \
  --region europe-west1 \
  --source . \
  --allow-unauthenticated \
  --timeout 3600 \
  --memory 2Gi \
  --set-env-vars SUPABASE_JWT_SECRET=your-jwt-secret-here
```

**Important:** Make sure to set `SUPABASE_JWT_SECRET` as an environment variable in Cloud Run:
- Cloud Run Console → Service → Edit & Deploy New Revision
- Variables & Secrets → Add Variable
- Name: `SUPABASE_JWT_SECRET`
- Value: Your JWT secret from Supabase

## 🔑 Key Features Implemented

### 1. Authentication System
- **Sign Up:** Email/password registration
- **Sign In:** JWT token-based authentication
- **Sign Out:** Token invalidation
- **Protected Routes:** All API endpoints require authentication

### 2. Multi-Tenancy
- **User Isolation:** All data scoped to user_id
- **RLS Policies:** Row-level security on all tables
- **Automatic User Init:** Triggers create user_settings, user_usage, etc. on signup

### 3. Usage Tracking
- **Free Tier Limits:**
  - 3 videos per day
  - 30 videos per month
- **Rate Limiting:** Enforced before automation trigger
- **Usage Display:** Shows remaining quota in UI

### 4. API Key Management
- **Per-User Keys:** Users can add their own API keys
- **Fallback to Defaults:** System keys used if user hasn't set their own
- **Secure Storage:** Keys encrypted at rest in Supabase
- **Settings UI:** User-friendly key management page

### 5. Video History
- **Complete Tracking:** All generated videos stored per user
- **Analytics:** Views, likes, comments tracked
- **Video Library:** User can browse their video history

### 6. Schedule Management
- **User-Specific:** Each user has their own schedules
- **Access Control:** Users can only see/edit/delete their own schedules

## 🧪 Testing Guide

### Step 6: Test the Complete Flow

1. **Test Registration:**
   ```bash
   curl -X POST "YOUR_URL/api/auth/signup" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'
   ```

2. **Test Login:**
   ```bash
   curl -X POST "YOUR_URL/api/auth/signin" \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123"}'
   ```
   
   Save the `access_token` from response.

3. **Test Authenticated Endpoint:**
   ```bash
   curl "YOUR_URL/api/auth/me" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

4. **Test Video Generation:**
   ```bash
   curl -X POST "YOUR_URL/api/automation/trigger" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"config":{"custom_topic":"Why cats purr","upload_to_youtube":false}}'
   ```

5. **Check Usage Limits:**
   ```bash
   curl "YOUR_URL/api/user/usage" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

## 📊 Monitoring

### Database Queries to Monitor

**Check Users:**
```sql
SELECT COUNT(*) as total_users FROM auth.users;
```

**Check Usage:**
```sql
SELECT 
  u.email,
  uu.videos_generated_today,
  uu.videos_generated_month,
  uu.plan_type
FROM auth.users u
JOIN user_usage uu ON u.id = uu.user_id
ORDER BY uu.videos_generated_month DESC;
```

**Check Video Generation:**
```sql
SELECT 
  u.email,
  COUNT(vh.id) as total_videos,
  SUM(CASE WHEN vh.upload_status = 'completed' THEN 1 ELSE 0 END) as successful_uploads
FROM auth.users u
LEFT JOIN video_history vh ON u.id = vh.user_id
GROUP BY u.email
ORDER BY total_videos DESC;
```

## 🐛 Troubleshooting

### Common Issues:

1. **"Invalid authentication credentials"**
   - Check `SUPABASE_JWT_SECRET` is set correctly
   - Verify token is being sent in Authorization header
   - Check token hasn't expired (24 hours default)

2. **"Daily limit reached"**
   - Check `user_usage` table
   - Manually reset if needed:
     ```sql
     UPDATE user_usage 
     SET videos_generated_today = 0 
     WHERE user_id = 'USER_UUID';
     ```

3. **"Row Level Security policy violation"**
   - Verify RLS policies were created correctly
   - Check user_id in JWT token matches row user_id
   - Ensure `auth.uid()` returns correct value

4. **Frontend: Infinite redirect loop**
   - Clear browser localStorage
   - Check AuthContext is properly mounted
   - Verify routes in App.js

## 🎯 Next Steps

### Recommended Enhancements:

1. **Email Verification:**
   - Enforce email verification before first use
   - Customize email templates in Supabase

2. **Subscription Plans:**
   - Integrate Stripe for payments
   - Add plan upgrade/downgrade flow
   - Implement usage limits per plan

3. **Admin Dashboard:**
   - Create admin role in database
   - Add user management UI
   - Monitor system-wide metrics

4. **API Rate Limiting:**
   - Add Redis for distributed rate limiting
   - Implement exponential backoff
   - Add IP-based limits

5. **Analytics:**
   - Track user engagement
   - Monitor video performance
   - A/B test different flows

## 📝 API Documentation

### All New Endpoints:

**Authentication:**
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/signin` - Login
- `POST /api/auth/signout` - Logout
- `GET /api/auth/me` - Get current user info

**User Settings:**
- `GET /api/user/settings` - Get API keys (masked)
- `PUT /api/user/settings` - Update API keys
- `GET /api/user/usage` - Get usage stats

**Automation (now auth-required):**
- `GET /api/status` - Get automation status
- `POST /api/automation/trigger` - Start automation
- `GET /api/automation/stop` - Stop automation

**Videos (now user-specific):**
- `GET /api/videos` - List user's videos
- `GET /api/videos/{video_id}` - Get video details

**Schedules (now user-specific):**
- `GET /api/schedules` - List user's schedules
- `POST /api/schedules` - Create schedule
- `GET /api/schedules/{schedule_id}` - Get schedule
- `PUT /api/schedules/{schedule_id}` - Update schedule
- `DELETE /api/schedules/{schedule_id}` - Delete schedule

All endpoints require `Authorization: Bearer <token>` header except auth endpoints.

## ✅ Migration Checklist

- [ ] Run `supabase_saas_schema.sql` in Supabase
- [ ] Verify all 6 tables created
- [ ] Enable Supabase Authentication
- [ ] Copy JWT Secret to `.env`
- [ ] Install new Python dependencies
- [ ] Deploy backend to Cloud Run
- [ ] Set `SUPABASE_JWT_SECRET` env var in Cloud Run
- [ ] Test signup flow
- [ ] Test login flow
- [ ] Test video generation with real user
- [ ] Verify usage tracking works
- [ ] Test all protected endpoints
- [ ] Deploy frontend (npm run build)
- [ ] Test complete user journey

## 🎉 Success Criteria

Your SaaS transformation is complete when:
1. ✅ New users can signup
2. ✅ Users can login and see dashboard
3. ✅ Each user sees only their own data
4. ✅ Usage limits are enforced
5. ✅ Users can add their own API keys
6. ✅ Video generation works per user
7. ✅ Schedules are user-isolated
8. ✅ No more "demo_user" hardcoded anywhere

---

**Need Help?** Check logs with:
```bash
# Backend logs
gcloud run logs read snip-z --region europe-west1 --limit=100

# Database logs (in Supabase Dashboard)
Logs → Postgres Logs
```

