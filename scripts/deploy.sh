#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build/lambda"
ZIP_FILE="$PROJECT_ROOT/build/lambda.zip"
FUNCTION_NAME="infra-explorer-analyzer"
BUCKET="infra-explorer-frontend-sandbox"
DISTRIBUTION_ID="E1MHNIQHI7VQ5F"
FRONTEND_URL="https://d2y8h0jbecvclg.cloudfront.net"

MODE="${1:-all}"

deploy_lambda() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🐍 LAMBDA"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo "🧹 Limpiando build anterior..."
    rm -rf "$BUILD_DIR" "$ZIP_FILE"
    mkdir -p "$BUILD_DIR"

    echo "📂 Copiando código fuente..."
    cp "$PROJECT_ROOT/src/lambda_handler.py" "$BUILD_DIR/"
    cp -r "$PROJECT_ROOT/src/core"       "$BUILD_DIR/"
    cp -r "$PROJECT_ROOT/src/extractors" "$BUILD_DIR/"
    cp -r "$PROJECT_ROOT/src/generators" "$BUILD_DIR/"
    cp -r "$PROJECT_ROOT/src/models"     "$BUILD_DIR/"
    cp -r "$PROJECT_ROOT/prompts"        "$BUILD_DIR/"

    echo "📦 Instalando dependencias Python..."
    pip3 install markdown -t "$BUILD_DIR" --quiet

    echo "🗜️  Creando ZIP..."
    cd "$BUILD_DIR"
    zip -r "$ZIP_FILE" . -x "*.pyc" "__pycache__/*" --quiet
    cd "$PROJECT_ROOT"

    echo "🚀 Subiendo código a Lambda..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --no-cli-pager > /dev/null

    echo "✅ Lambda desplegada: $FUNCTION_NAME"
}

deploy_frontend() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🌐 FRONTEND"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo "📤 Sincronizando archivos con S3..."
    aws s3 sync "$PROJECT_ROOT/frontend/" "s3://$BUCKET/" --delete

    echo "🔄 Invalidando caché de CloudFront..."
    aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*" \
        --no-cli-pager \
        --output text \
        --query 'Invalidation.Status' > /dev/null

    echo "✅ Frontend desplegado: $FRONTEND_URL"
}

case "$MODE" in
    lambda)
        deploy_lambda
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        deploy_lambda
        deploy_frontend
        ;;
    *)
        echo "Uso: ./scripts/deploy.sh [lambda|frontend|all]"
        echo "  lambda   — solo código Python de la Lambda"
        echo "  frontend — solo HTML/JS/CSS a S3 + CloudFront"
        echo "  all      — ambos (por defecto)"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deploy finalizado."
