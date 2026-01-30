#!/bin/bash
# =============================================================================
# Setup Webhook Tunnel for Zoice Voice AI Integration
# Uses ngrok to expose local PRM service for webhook callbacks
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🔗 Setting up Webhook Tunnel for Zoice Integration..."

# Check if .env exists and has ngrok token
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

source .env
if [ -z "$NGROK_AUTHTOKEN" ] || [ "$NGROK_AUTHTOKEN" = "your-ngrok-auth-token" ]; then
    echo ""
    echo "⚠️  NGROK_AUTHTOKEN not configured!"
    echo ""
    echo "To enable webhook testing:"
    echo "1. Sign up at https://dashboard.ngrok.com/"
    echo "2. Get your auth token"
    echo "3. Add it to .env: NGROK_AUTHTOKEN=your-token"
    echo ""
    exit 1
fi

# Start ngrok with dev services
echo "🐳 Starting services with ngrok tunnel..."
docker compose -f docker-compose.dev.yml --profile webhooks up -d

# Wait for ngrok to start
echo "⏳ Waiting for ngrok to initialize..."
sleep 5

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL. Check the ngrok dashboard at http://localhost:4040"
    exit 1
fi

echo ""
echo "✅ Webhook Tunnel Ready!"
echo ""
echo "🌐 Public URL: $NGROK_URL"
echo ""
echo "📞 Zoice Webhook Endpoints:"
echo "   • Call Start:      $NGROK_URL/api/v1/prm/voice/webhook/call-start"
echo "   • Call End:        $NGROK_URL/api/v1/prm/voice/webhook/call-end"
echo "   • Transcription:   $NGROK_URL/api/v1/prm/voice/webhook/transcription"
echo "   • Recording:       $NGROK_URL/api/v1/prm/voice/webhook/recording"
echo ""
echo "💡 Configure these URLs in your Zoice dashboard:"
echo "   https://api2.zoice.ai/plivo/docs"
echo ""
echo "📊 ngrok Dashboard: http://localhost:4040"
echo ""
