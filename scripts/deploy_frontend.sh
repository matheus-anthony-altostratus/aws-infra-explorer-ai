#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUCKET="infra-explorer-frontend-sandbox"
DISTRIBUTION_ID="E1MHNIQHI7VQ5F"

echo "🚀 Subiendo frontend a S3..."
aws s3 sync "$PROJECT_ROOT/frontend/" "s3://$BUCKET/" --delete

echo "🔄 Invalidando caché de CloudFront..."
aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --no-cli-pager

echo "✅ Frontend desplegado: https://d2y8h0jbecvclg.cloudfront.net"
