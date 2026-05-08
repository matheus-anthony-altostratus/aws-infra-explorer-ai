#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build/lambda"
ZIP_FILE="$PROJECT_ROOT/build/lambda.zip"
FUNCTION_NAME="infra-explorer-analyzer"

echo "🧹 Limpiando build anterior..."
rm -rf "$BUILD_DIR" "$ZIP_FILE"
mkdir -p "$BUILD_DIR"

echo "📦 Copiando código fuente..."
cp "$PROJECT_ROOT/src/lambda_handler.py" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/src/core" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/src/extractors" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/src/generators" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/src/models" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/prompts" "$BUILD_DIR/"

echo "📦 Instalando dependencias..."
pip3 install markdown -t "$BUILD_DIR" --quiet

echo "🗜️  Creando ZIP..."
cd "$BUILD_DIR"
zip -r "$ZIP_FILE" . -x "*.pyc" "__pycache__/*" --quiet

echo "🚀 Desplegando a Lambda..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file "fileb://$ZIP_FILE" \
    --no-cli-pager

echo "✅ Deploy completado: $FUNCTION_NAME"
