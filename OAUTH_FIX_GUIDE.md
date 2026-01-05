# Fix OAuth Redirect URI Mismatch for Cloud Run

## Problem
Getting error: `Error 400: redirect_uri_mismatch` when trying to authenticate with Google on Cloud Run.

## Root Cause
The application is using the out-of-band flow (`urn:ietf:wg:oauth:2.0:oob`) which is deprecated and doesn't work with web applications. Cloud Run requires a proper HTTPS redirect URI.

## Solution

### Step 1: Get Your Cloud Run URL
```bash
# Get your Cloud Run service URL
gcloud run services describe YOUR_SERVICE_NAME --region YOUR_REGION --format='value(status.url)'
```

Example output: `https://youtube-automation-abc123-uc.a.run.app`

### Step 2: Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Find your OAuth 2.0 Client ID (the one you're using for YouTube API)
4. Click **Edit**
5. Under **Authorized redirect URIs**, add:
   ```
   https://YOUR-CLOUD-RUN-URL.run.app/youtube/auth/callback
   ```
   
   For example:
   ```
   https://youtube-automation-abc123-uc.a.run.app/youtube/auth/callback
   ```

6. **Also add** (for local development):
   ```
   http://localhost:8000/youtube/auth/callback
   http://localhost:3000/youtube/auth/callback
   ```

7. Click **Save**

### Step 3: Update Cloud Run Environment Variable

Set the redirect URI in your Cloud Run environment variables:

```bash
gcloud run services update YOUR_SERVICE_NAME \
  --region YOUR_REGION \
  --update-env-vars YOUTUBE_REDIRECT_URI=https://YOUR-CLOUD-RUN-URL.run.app/youtube/auth/callback
```

### Step 4: Update Local .env File (Optional)

For local development, update your `.env` file:

```env
YOUTUBE_REDIRECT_URI=http://localhost:8000/youtube/auth/callback
```

### Step 5: Verify the Setup

After making these changes:

1. Redeploy your Cloud Run service (if needed)
2. Try the OAuth flow again from the frontend
3. You should now be redirected properly after Google authentication

## Common Issues

### Issue 1: Still getting redirect_uri_mismatch
**Solution**: Make sure the URIs match EXACTLY (including https vs http, trailing slashes, etc.)
- Check what's in Google Console
- Check what's set in Cloud Run env vars
- Check the browser network tab to see what redirect_uri is being sent

### Issue 2: Works locally but not on Cloud Run
**Solution**: Make sure you've added BOTH the Cloud Run URL and localhost URLs to Google Console

### Issue 3: "Origin not allowed" error
**Solution**: In Google Cloud Console → OAuth consent screen, add your Cloud Run URL to the authorized domains

## Testing

Test the OAuth flow:
```bash
# Check current environment variable
gcloud run services describe YOUR_SERVICE_NAME \
  --region YOUR_REGION \
  --format='value(spec.template.spec.containers[0].env)' | grep YOUTUBE_REDIRECT_URI

# Test the auth start endpoint
curl https://YOUR-CLOUD-RUN-URL.run.app/youtube/auth/start?user_id=test_user
```

## Additional Configuration

If you're using a custom domain, update the redirect URI to use your custom domain instead of the Cloud Run URL:

```
https://yourdomain.com/youtube/auth/callback
```

And add this to Google Console as well.

## Security Note

Never commit your actual OAuth credentials to git. Always use environment variables and keep them secure in:
- Cloud Run environment variables
- GitHub Secrets (for CI/CD)
- Local .env file (gitignored)
