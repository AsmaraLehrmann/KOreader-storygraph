# StoryGraph Sync

Automatically sync your KOReader reading progress to StoryGraph using Google Cloud Run (free tier).

## Features

- ✅ Syncs reading progress from KOReader to StoryGraph
- ✅ Runs on Google Cloud Run (completely free for this use case)
- ✅ Automatic hourly syncing between 8am-11pm
- ✅ Can also be triggered manually from your Kindle
- ✅ Uses Selenium for browser automation
- ✅ Integrates with KoInsight or works standalone

## Architecture

```
┌─────────────────┐
│  Kindle         │
│  KOReader       │──────┐
└─────────────────┘      │
                         │ Reading data
                         ▼
               ┌─────────────────────┐
               │  Google Cloud Run   │
               │                     │
               │  StoryGraph Sync    │
               │  (This service)     │
               └─────────────────────┘
                         │
                         │ Browser automation
                         ▼
               ┌─────────────────────┐
               │  StoryGraph.com     │
               │  (Updates progress) │
               └─────────────────────┘
```

## Prerequisites

1. **Google Cloud Account** (free tier is sufficient)
2. **StoryGraph Account**
3. **KOReader** on your Kindle (jailbroken)
4. **Docker** (for local testing, optional)

## Quick Start

### 1. Clone and Configure

```bash
# Create .env file from example
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Add your StoryGraph credentials:
```
STORYGRAPH_EMAIL=your-email@example.com
STORYGRAPH_PASSWORD=your-password
```

### 2. Deploy to Google Cloud Run

```bash
# Edit deploy.sh to set your project ID
nano deploy.sh
# Change: PROJECT_ID="your-gcp-project-id"

# Make sure you have gcloud CLI installed
# https://cloud.google.com/sdk/docs/install

# Set your credentials as environment variables
export STORYGRAPH_EMAIL="your-email@example.com"
export STORYGRAPH_PASSWORD="your-password"

# Run deployment
./deploy.sh
```

The script will:
- Build the Docker image
- Push to Google Container Registry
- Deploy to Cloud Run
- Give you a service URL

### 3. Set Up Automatic Hourly Syncing

```bash
# Replace with your actual service URL
./setup-scheduler.sh https://storygraph-sync-xxx.run.app
```

This creates Cloud Scheduler jobs that trigger syncing every hour from 8am-11pm.

## Testing

### Test Locally (Optional)

```bash
# Build and run with Docker Compose
docker-compose up

# In another terminal, test the sync
curl -X POST http://localhost:8080/sync
```

### Test on Cloud Run

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe storygraph-sync --platform managed --region us-central1 --format 'value(status.url)')

# Health check
curl $SERVICE_URL

# Trigger a sync
curl -X POST $SERVICE_URL/sync
```

## Usage Options

### Option 1: Automatic Hourly Sync (Recommended)

Once Cloud Scheduler is set up, it will automatically sync every hour. No action needed!

### Option 2: Manual Trigger from Computer

```bash
curl -X POST https://your-service-url.run.app/sync
```

### Option 3: Trigger from Kindle (KUAL Extension)

Create a KUAL extension that sends data directly:

```bash
#!/bin/sh
# In your KUAL extension: /mnt/us/extensions/storygraph-sync/bin/sync.sh

SERVICE_URL="https://your-service-url.run.app"

# Extract KOReader data
sqlite3 /mnt/us/.adds/koreader/statistics.sqlite3 \
  "SELECT json_object('title', title, 'author', authors, 'current_page', last_page, 'total_pages', pages, 'progress', (last_page*100.0/pages)) 
   FROM books 
   WHERE last_open > datetime('now', '-7 days');" > /tmp/books.json

# Send to service
wget --post-file=/tmp/books.json \
     --header='Content-Type: application/json' \
     ${SERVICE_URL}/manual-sync

eips -c
eips 10 10 "Synced to StoryGraph!"
sleep 2
```

## How It Works

1. **Data Source**: Reads from KoInsight database or receives data directly from Kindle
2. **Processing**: Extracts book title, author, and reading progress
3. **StoryGraph Update**: 
   - Logs into StoryGraph using Selenium
   - Searches for each book
   - Updates reading progress
4. **Results**: Returns summary of what was synced

## Configuration

### Environment Variables

- `STORYGRAPH_EMAIL`: Your StoryGraph login email
- `STORYGRAPH_PASSWORD`: Your StoryGraph password
- `KOINSIGHT_DB_PATH`: Path to KoInsight database (default: `/app/data/koinsight.db`)
- `PORT`: Port to run on (set by Cloud Run, default: 8080)

### Timezone

By default, the scheduler runs on `America/Chicago` time. To change:

Edit `setup-scheduler.sh` and modify:
```bash
--time-zone="America/New_York"  # Or your timezone
```

## Cost Estimate

### Google Cloud Run Free Tier

- **CPU**: 180,000 vCPU-seconds/month (you'll use ~1%)
- **Memory**: 360,000 GiB-seconds/month (you'll use ~1%)
- **Requests**: 2 million/month (you'll use ~500)

**Estimated cost: $0.00/month** ✨

Your usage:
- 16 syncs/day (8am-11pm)
- ~30 seconds per sync
- ~480 syncs/month
- Well within free tier!

## Troubleshooting

### Login Failed

Make sure your StoryGraph credentials are correct:
```bash
# Update credentials
gcloud run services update storygraph-sync \
  --region us-central1 \
  --set-env-vars "STORYGRAPH_EMAIL=new-email@example.com,STORYGRAPH_PASSWORD=new-password"
```

### Book Not Found

The service searches by title and author. If a book isn't found:
1. Check the book exists on StoryGraph
2. Ensure title/author match exactly
3. Try adding the book manually first on StoryGraph

### ChromeDriver Issues

Cloud Run includes Chrome and ChromeDriver. If there are issues:
1. Check logs: `gcloud run logs read --service storygraph-sync --region us-central1`
2. Ensure headless mode is working
3. May need to update Chrome version in Dockerfile

### View Logs

```bash
# Real-time logs
gcloud run logs tail --service storygraph-sync --region us-central1

# Recent logs
gcloud run logs read --service storygraph-sync --region us-central1 --limit 50
```

## API Endpoints

### `GET /`
Health check endpoint
```bash
curl https://your-service.run.app/
```

### `POST /sync`
Trigger sync from KoInsight database
```bash
curl -X POST https://your-service.run.app/sync
```

### `POST /manual-sync`
Sync with data provided directly
```bash
curl -X POST https://your-service.run.app/manual-sync \
  -H "Content-Type: application/json" \
  -d '{
    "books": [
      {
        "title": "Project Hail Mary",
        "author": "Andy Weir",
        "current_page": 234,
        "total_pages": 476,
        "progress": 49.2
      }
    ]
  }'
```

## Updating the Service

```bash
# Make changes to app.py
# Then redeploy
./deploy.sh
```

## Uninstalling

```bash
# Delete Cloud Run service
gcloud run services delete storygraph-sync --region us-central1

# Delete scheduler jobs
for hour in {8..23}; do
  gcloud scheduler jobs delete storygraph-sync-${hour}00 --location us-central1 --quiet
done

# Delete Docker image
gcloud container images delete gcr.io/your-project-id/storygraph-sync
```

## Contributing

Feel free to open issues or submit pull requests!

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

- Built to work with [KoInsight](https://github.com/GeorgeSG/KoInsight)
- Inspired by the KOReader community
- Uses StoryGraph's web interface (no official API yet)
