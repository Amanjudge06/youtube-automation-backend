# Scheduler Deployment Checklist

## Current Issues Identified

### 1. ✅ Code Updated (DONE)
- Scheduler now supports Supabase persistence
- Changes committed and pushed to GitHub

### 2. ⚠️ Supabase Table (NEEDS VERIFICATION)
**Status:** Unknown - need to verify if table exists

**To Check:**
Run this in your Cloud Shell:
```bash
curl -X GET "https://xahdiwtsshyxaqwksbna.supabase.co/rest/v1/schedules?select=*" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI"
```

**If you see error "relation does not exist":**
1. Go to https://supabase.com/dashboard/project/xahdiwtsshyxaqwksbna/editor
2. Click "SQL Editor" in left sidebar
3. Click "+ New Query"
4. Copy contents of `supabase_schedules_schema.sql` from your repo
5. Paste and click "Run"

### 3. ❌ Cloud Run Deployment (NEEDS REDEPLOY)
**Status:** Current deployment doesn't have the new code

**Required Action:**
```bash
cd ~/youtube-automation-backend  # or wherever your repo is cloned
git pull origin main
gcloud run deploy snip-z --region europe-west1
```

### 4. ❌ FFmpeg Error (NEEDS INVESTIGATION)
**Status:** FFmpeg not found despite being in Dockerfile

**Possible Causes:**
- Old Docker image cached
- Deployment using wrong Dockerfile
- Build failed silently

**Solution:**
Force rebuild during deployment:
```bash
gcloud run deploy snip-z \
  --region europe-west1 \
  --source . \
  --no-cache
```

## Step-by-Step Fix

### Step 1: Verify/Create Supabase Table
```bash
# Test if table exists
curl -X GET "https://xahdiwtsshyxaqwksbna.supabase.co/rest/v1/schedules?select=schedule_id" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI"
```

If error, create table:
1. Visit https://supabase.com/dashboard/project/xahdiwtsshyxaqwksbna/sql/new
2. Paste SQL from `supabase_schedules_schema.sql`
3. Run it

### Step 2: Clone/Update Repository
```bash
# If not cloned yet
git clone https://github.com/Amanjudge06/youtube-automation-backend.git
cd youtube-automation-backend

# If already cloned
cd youtube-automation-backend
git pull origin main
```

### Step 3: Deploy with Force Rebuild
```bash
gcloud run deploy snip-z \
  --region europe-west1 \
  --source . \
  --platform managed \
  --allow-unauthenticated \
  --no-cache
```

Wait 3-5 minutes for deployment to complete.

### Step 4: Verify Deployment
```bash
# Check logs for scheduler initialization
gcloud run services logs read snip-z --region europe-west1 --limit 50 | grep -i "scheduler\|persistence\|supabase"

# Look for this line:
# "📊 Using Supabase for schedule persistence"
```

### Step 5: Test Creating a Schedule
1. Go to https://snip-z-280443511832.europe-west1.run.app
2. Click "Schedules" tab
3. Click "+ Add Schedule"
4. Create a schedule
5. Refresh the page - schedule should still be there
6. Create another schedule - both should be visible

### Step 6: Verify in Supabase
```bash
# Check schedules are in database
curl -X GET "https://xahdiwtsshyxaqwksbna.supabase.co/rest/v1/schedules?select=*" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI" | python3 -m json.tool
```

## Troubleshooting

### If schedules still disappear:
1. Check deployment logs: `gcloud run services logs tail snip-z --region europe-west1`
2. Look for "Using Supabase" or "Using local file"
3. If "local file", environment variables might not be set correctly

### If FFmpeg error persists:
```bash
# Check if FFmpeg is in the container
gcloud run services describe snip-z --region europe-west1 --format=yaml | grep image

# Force complete rebuild
gcloud builds submit --tag gcr.io/gen-lang-client-0934292943/snip-z
gcloud run deploy snip-z --image gcr.io/gen-lang-client-0934292943/snip-z --region europe-west1
```

### If automation fails to run:
- Check all API keys are set in Cloud Run environment variables
- Verify YouTube refresh token is valid
- Check logs for specific error messages

## Quick Commands Reference

```bash
# View real-time logs
gcloud run services logs tail snip-z --region europe-west1

# Redeploy
gcloud run deploy snip-z --region europe-west1 --source .

# Check environment variables
gcloud run services describe snip-z --region europe-west1 --format="value(spec.template.spec.containers[0].env)"

# Force rebuild
gcloud run deploy snip-z --region europe-west1 --source . --no-cache
```

## Success Criteria

✅ Supabase table exists
✅ Logs show "Using Supabase for schedule persistence"
✅ Can create multiple schedules via frontend
✅ Schedules persist after page refresh
✅ Schedules visible in Supabase database
✅ No FFmpeg errors in logs
✅ Schedules execute at specified times

Once all criteria are met, the scheduler will work perfectly! 🎉
