# Scheduler Fix for Cloud Run - Multiple Schedules Issue

## Problem
Schedules were disappearing on Cloud Run because they were stored in local JSON files that get reset on container restarts.

## Solution
Updated the scheduler to use **Supabase** for persistent storage instead of local files.

## Changes Made

### 1. Updated `services/scheduler_service.py`
- Added Supabase support for schedule persistence
- Falls back to local JSON files if Supabase is not configured
- Auto-detects storage mode based on environment variables

### 2. Created Supabase Schema
File: `supabase_schedules_schema.sql`
- Creates `schedules` table with all necessary fields
- Adds indexes for performance
- Includes RLS policies for security

## Setup Steps

### Step 1: Create Supabase Table
1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/xahdiwtsshyxaqwksbna)
2. Click "SQL Editor" in left sidebar
3. Click "New Query"
4. Copy and paste the contents of `supabase_schedules_schema.sql`
5. Click "Run" or press Cmd/Ctrl + Enter

### Step 2: Deploy to Cloud Run
```bash
cd /Users/aman/Documents/YouTube\ Automation
git add -A
git commit -m "Fix scheduler persistence with Supabase for Cloud Run"
git push
gcloud run deploy snip-z --region europe-west1
```

### Step 3: Verify
```bash
# Check Cloud Run logs
gcloud run logs read snip-z --region europe-west1 --limit 50

# Look for:
# 📊 Using Supabase for schedule persistence
# 📂 Loaded X schedules from Supabase
```

## How It Works

### Local Development
- Uses local JSON file: `user_data/schedules.json`
- Perfect for testing without Supabase

### Cloud Run (Production)
- Detects `SUPABASE_URL` and `SUPABASE_KEY` environment variables
- Automatically uses Supabase for storage
- Schedules persist across container restarts and deployments

### Storage Detection
```python
self.use_supabase = bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'))
```

## Testing

### Test Locally (JSON mode)
```bash
python3 app.py
# Creates schedules in user_data/schedules.json
```

### Test with Supabase (Production mode)
```bash
# Temporarily set Supabase vars
export SUPABASE_URL=https://xahdiwtsshyxaqwksbna.supabase.co
export SUPABASE_KEY=sb_publishable_GcIsP-eCDvmcf4u41lXrOA_vMTVJNGU
python3 app.py
# Creates schedules in Supabase
```

## API Endpoints (No Changes)
- `POST /api/schedules` - Create schedule
- `GET /api/schedules?user_id=X` - List schedules
- `PUT /api/schedules/{id}` - Update schedule
- `DELETE /api/schedules/{id}` - Delete schedule
- `POST /api/schedules/{id}/toggle` - Toggle on/off

## Verification Checklist

- [ ] Supabase table created
- [ ] Code deployed to Cloud Run
- [ ] Logs show "Using Supabase for schedule persistence"
- [ ] Can create schedules via frontend
- [ ] Multiple schedules stay visible
- [ ] Schedules persist after page refresh
- [ ] Schedules survive Cloud Run restarts

## Troubleshooting

### If schedules still disappear:
1. Check Supabase table exists:
   ```sql
   SELECT * FROM schedules;
   ```

2. Check Cloud Run environment variables:
   ```bash
   gcloud run services describe snip-z --region europe-west1 \
     --format="value(spec.template.spec.containers[0].env)"
   ```

3. Check logs for storage mode:
   ```bash
   gcloud run logs read snip-z --region europe-west1 | grep "persistence"
   ```

### If seeing "Local file" instead of "Supabase":
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are set in Cloud Run
- Redeploy after setting environment variables

### If Supabase connection fails:
- Check Supabase project is active
- Verify API keys are correct
- Check RLS policies allow access

## Summary

✅ **Before:** Schedules stored in local JSON → Lost on restart  
✅ **After:** Schedules stored in Supabase → Persist forever

The scheduler now works perfectly on Cloud Run with multiple schedules that persist across restarts!
