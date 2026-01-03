# Deployment Guide for Snip-Z Automation

This guide explains how to deploy the YouTube Automation system to a production environment.

## Prerequisites

1.  **Docker**: Ensure Docker and Docker Compose are installed on your target server.
2.  **API Keys**: You need all your API keys ready (OpenAI, ElevenLabs, Supabase, etc.).

## Option 1: Deploy to a VPS (DigitalOcean, Linode, AWS EC2) - Recommended

This gives you full control and is the most cost-effective for running FFmpeg tasks.

1.  **Provision a Server**:
    *   Ubuntu 22.04 LTS is recommended.
    *   At least 2GB RAM (4GB recommended for video processing).

2.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

3.  **Setup Environment Variables**:
    *   Copy the example file:
        ```bash
        cp .env.example .env
        ```
    *   Edit `.env` and add your actual keys:
        ```bash
        nano .env
        ```

4.  **Build and Run**:
    ```bash
    docker-compose up -d --build
    ```

5.  **Access the App**:
    *   Open `http://<your-server-ip>:8000` in your browser.

## Option 2: Deploy to Render.com (PaaS)

Render supports Docker and is easier to set up but might be more expensive for high usage.

1.  **Create a Web Service**:
    *   Connect your GitHub repository.
    *   Select "Docker" as the runtime.

2.  **Environment Variables**:
    *   Add all your keys (OPENAI_API_KEY, etc.) in the Render dashboard.

3.  **Disk Storage (Important)**:
    *   Since this app generates video files, you need persistent storage if you want to keep them.
    *   Add a "Disk" in Render and mount it to `/app/output`.

## Option 3: Serverless Containers (Google Cloud Run) - Best for Scaling

If you want a "Serverless" experience (scale to zero, pay per use) similar to Edge Functions but with support for Python and FFmpeg.

1.  **Install Google Cloud SDK**.
2.  **Authenticate**:
    ```bash
    gcloud auth login
    gcloud config set project <your-project-id>
    ```
3.  **Deploy**:
    ```bash
    gcloud run deploy snip-z-automation \
      --source . \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --memory 2Gi \
      --timeout 300 \
      --set-env-vars="SUPABASE_URL=...,SUPABASE_KEY=..."
    ```
    *Note: You must pass all environment variables using the `--set-env-vars` flag.*

### Why not Supabase Edge Functions?
Supabase Edge Functions run on **Deno (JavaScript)** and have a strict execution time limit. They **cannot** run Python code or install system dependencies like **FFmpeg**, which are required for this video generation engine. Google Cloud Run is the correct "Serverless" alternative for heavy processing tasks.

## Final Checks Checklist

- [ ] **API Keys**: Ensure `.env` is populated and NOT committed to Git.
- [ ] **Supabase**: Ensure your Supabase project has the `videos` table and Storage bucket created.
- [ ] **YouTube Auth**: For the first run, you might need to authenticate locally to generate `youtube_credentials.json` and upload that file to your server (or mount it via volume).

## Troubleshooting

*   **Logs**: View logs with `docker-compose logs -f`.
*   **Permissions**: If you see permission errors with `output/` folder, run `chmod 777 output temp logs`.
