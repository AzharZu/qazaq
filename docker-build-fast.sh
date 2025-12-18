#!/bin/bash
# Optimized Docker build script for Qazaq platform
# Enables BuildKit for better caching and parallelization

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Optimized Qazaq Docker Build"
echo "=================================="
echo ""

# Enable Docker BuildKit for better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export BUILDKIT_PROGRESS=plain

echo "📦 Building services with optimizations enabled..."
echo "   - Docker BuildKit enabled (better caching)"
echo "   - Parallel builds enabled"
echo "   - Layer caching optimized"
echo ""

# Build with BuildKit
if docker-compose build --progress=plain "$@"; then
    echo ""
    echo "✅ Build completed successfully!"
    echo ""
    echo "💡 Next steps:"
    echo "   $ docker-compose up -d"
    echo "   $ ./health-check.sh"
else
    echo ""
    echo "❌ Build failed. Check logs above."
    exit 1
fi
