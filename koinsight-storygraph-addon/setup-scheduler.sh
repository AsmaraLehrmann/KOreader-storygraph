#!/bin/bash
# Set up Google Cloud Scheduler to run sync every hour between 8am-11pm

set -e

SERVICE_URL=$1

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Usage: ./setup-scheduler.sh <service-url>"
    echo "   Example: ./setup-scheduler.sh https://storygraph-sync-xxx.run.app"
    exit 1
fi

PROJECT_ID="your-gcp-project-id"
REGION="us-central1"

echo "⏰ Setting up Cloud Scheduler jobs..."

# Create scheduler jobs for each hour between 8am-11pm
for hour in {8..23}; do
    JOB_NAME="storygraph-sync-${hour}00"
    SCHEDULE="0 ${hour} * * *"  # Every day at this hour
    
    echo "   Creating job: ${JOB_NAME} (${hour}:00)"
    
    gcloud scheduler jobs create http ${JOB_NAME} \
        --location=${REGION} \
        --schedule="${SCHEDULE}" \
        --uri="${SERVICE_URL}/sync" \
        --http-method=POST \
        --time-zone="America/Chicago" \
        --description="Sync KOReader progress to StoryGraph at ${hour}:00" \
        --attempt-deadline=300s \
        || echo "   Job ${JOB_NAME} already exists, skipping..."
done

echo "✅ Cloud Scheduler setup complete!"
echo ""
echo "📋 Created jobs for:"
echo "   - Every hour from 8:00 AM to 11:00 PM"
echo "   - Timezone: America/Chicago (adjust in script if needed)"
echo ""
echo "🔍 View your jobs:"
echo "   gcloud scheduler jobs list --location=${REGION}"
echo ""
echo "▶️  Test a job manually:"
echo "   gcloud scheduler jobs run storygraph-sync-0800 --location=${REGION}"
echo ""
echo "🗑️  To delete all jobs:"
echo "   for hour in {8..23}; do"
echo "     gcloud scheduler jobs delete storygraph-sync-\${hour}00 --location=${REGION} --quiet"
echo "   done"
