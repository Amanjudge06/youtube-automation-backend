# YouTube API Setup Guide

## Overview
This guide will help you set up YouTube Data API v3 credentials to enable automatic video uploads to YouTube.

## Prerequisites
- Google account
- Access to Google Cloud Console
- The video generation pipeline should be working

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a Project" → "New Project"
3. Enter project name: "YouTube Automation"
4. Click "Create"

### 2. Enable YouTube Data API v3

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "+ Create Credentials" → "OAuth client ID"
3. If prompted, configure the consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in required fields:
     - App name: "YouTube Automation"
     - User support email: Your email
     - Developer contact: Your email
   - Save and continue through the scopes (no changes needed)
   - Add your email as a test user
   - Save and continue
4. Back to credentials, select "Desktop application"
5. Name it: "YouTube Upload Client"
6. Click "Create"

### 4. Configure Credentials in the Application

1. Copy the Client ID and Client Secret from the credentials page
2. Open `config.py` in your project
3. Update these lines:
   ```python
   YOUTUBE_CLIENT_ID = "your-client-id-here"
   YOUTUBE_CLIENT_SECRET = "your-client-secret-here"
   ```

### 5. Test Authentication

Run the authentication test:
```bash
python upload_video.py --test-auth
```

This will:
- Open a browser window for Google OAuth
- Ask you to sign in and authorize the application
- Save your credentials for future use

### 6. Upload Your First Video

Once authentication is working, upload your generated video:
```bash
python upload_video.py
```

This will upload the latest video with SEO-optimized metadata.

## Security Notes

- Keep your Client ID and Client Secret secure
- The OAuth token is saved locally in `youtube_token.pickle`
- Never commit these credentials to version control
- Consider using environment variables for production

## Environment Variables (Alternative Setup)

Instead of editing `config.py` directly, you can set environment variables:

```bash
export YOUTUBE_CLIENT_ID="your-client-id"
export YOUTUBE_CLIENT_SECRET="your-client-secret"
```

## Troubleshooting

### Common Issues

1. **"API not enabled"**
   - Ensure YouTube Data API v3 is enabled in Google Cloud Console

2. **"Quota exceeded"**
   - YouTube API has daily quotas. Wait 24 hours or request quota increase

3. **"Invalid credentials"**
   - Double-check your Client ID and Client Secret
   - Delete `youtube_token.pickle` and re-authenticate

4. **"Redirect URI mismatch"**
   - Ensure redirect URI is set to `http://localhost:8080`

### Quota Limits

- YouTube Data API v3 has a default quota of 10,000 units per day
- A video upload typically costs 1,600 units
- This allows ~6 uploads per day with the default quota

## Features Included

### SEO Optimization
- Optimized titles with trending keywords
- Comprehensive descriptions with key points
- Relevant tags based on topic analysis
- Trending hashtags

### Automatic Enhancements
- Custom thumbnail generation from video frames
- Timestamp integration in descriptions
- Category-specific optimizations
- Location-based tags when applicable

### Upload Settings
- Default privacy: Public (configurable)
- Category: Entertainment (configurable)
- License: Creative Commons (configurable)
- Embeddable: Yes
- Made for Kids: No (configurable)

## Configuration Options

Edit `config.py` to customize upload behavior:

```python
YOUTUBE_CONFIG = {
    "privacy_status": "public",  # "private", "unlisted", "public"
    "category_id": "24",  # Entertainment
    "made_for_kids": False,
    # ... more options
}
```

## Support

If you encounter issues:
1. Check the logs in `logs/youtube_automation.log`
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Verify your Google Cloud project settings
4. Test authentication separately before uploading