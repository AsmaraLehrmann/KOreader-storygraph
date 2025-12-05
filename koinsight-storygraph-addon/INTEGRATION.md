# StoryGraph Sync for KoInsight

Automatically sync your reading progress from KoInsight to StoryGraph.

## What This Does

This service runs alongside KoInsight and automatically syncs your reading progress to StoryGraph:
- Reads data from KoInsight's database
- Logs into StoryGraph
- Updates your reading progress for all books
- Runs automatically every hour (8am-11pm)

## Integration with KoInsight

This is a **companion service** that works with KoInsight:

```
KoInsight (main app)
    │
    ├─ Stores reading data in SQLite
    │
    └─ This service reads that data
        └─ Syncs to StoryGraph
```

## Quick Deploy

### Option 1: Add to KoInsight's docker-compose.yml

Add this service to your existing KoInsight setup:

```yaml
services:
  koinsight:
    # ... your existing KoInsight config ...
  
  storygraph-sync:
    build: ./storygraph-sync
    environment:
      - STORYGRAPH_EMAIL=${STORYGRAPH_EMAIL}
      - STORYGRAPH_PASSWORD=${STORYGRAPH_PASSWORD}
      - KOINSIGHT_DB_PATH=/app/data/koinsight.db
    volumes:
      - ./data:/app/data  # Share KoInsight's data directory
    ports:
      - "8081:8080"
    depends_on:
      - koinsight
```

### Option 2: Deploy Separately to Google Cloud Run

See the main README.md for full deployment instructions.

## Setup

1. **Clone into your KoInsight fork:**
   ```bash
   cd your-koinsight-fork
   mkdir storygraph-sync
   # Extract the contents of this zip into that folder
   ```

2. **Configure credentials:**
   ```bash
   # Add to your .env file
   STORYGRAPH_EMAIL=your-email@example.com
   STORYGRAPH_PASSWORD=your-password
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Test the sync:**
   ```bash
   curl -X POST http://localhost:8081/sync
   ```

## Automated Syncing

### With Docker Compose (Local)

Add a cron job on your host machine:

```bash
# Edit crontab
crontab -e

# Add hourly sync between 8am-11pm
0 8-23 * * * curl -X POST http://localhost:8081/sync
```

### With Google Cloud Run (Recommended)

Deploy both KoInsight and this service to Cloud Run, then use Cloud Scheduler:

```bash
./setup-scheduler.sh https://your-storygraph-sync-url.run.app
```

## API Endpoints

### `POST /sync`
Triggers a sync from KoInsight database to StoryGraph.

```bash
curl -X POST http://localhost:8081/sync
```

### `GET /`
Health check endpoint.

```bash
curl http://localhost:8081/
```

## Database Schema

This service expects KoInsight's database to have a table with these fields:
- `title` - Book title
- `authors` - Book author(s)
- `pages` - Total pages
- `last_page` - Current page
- `last_open` - Last time book was opened

If KoInsight's schema differs, you may need to adjust the query in `app.py`.

## Troubleshooting

### "Database not found"
Make sure the volumes are shared correctly between KoInsight and this service.

### "Login failed"
Check your StoryGraph credentials in the environment variables.

### "Book not found on StoryGraph"
The book might not exist on StoryGraph yet - add it manually first.

## Contributing

Since this is an addon to KoInsight, consider:
1. Keeping it as a separate service (current approach)
2. Or proposing integration into KoInsight core
3. Or creating a KoInsight plugin architecture

## License

MIT License
