#!/bin/bash
# Quick test script to verify Supabase schedules table

echo "Testing Supabase schedules table..."
echo ""

# Test if table exists and can be queried
curl -X GET "https://xahdiwtsshyxaqwksbna.supabase.co/rest/v1/schedules?select=*" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaGRpd3Rzc2h5eGFxd2tzYm5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU5ODU3NjgsImV4cCI6MjA1MTU2MTc2OH0.bZj2FDPVfH_Dv5dQaXw7jrXBrCrB8FfGGBCB5_AzrNI" \
  2>/dev/null | python3 -m json.tool

echo ""
echo "If you see an error about 'relation \"schedules\" does not exist',"
echo "you need to create the table by running the SQL in supabase_schedules_schema.sql"
