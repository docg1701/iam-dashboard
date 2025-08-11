#!/bin/bash

# Database seeding script for IAM Dashboard
# Usage: ./run_seed.sh [--force]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 IAM Dashboard Database Seeder${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if we're in the right directory
if [[ ! -f "$API_DIR/pyproject.toml" ]]; then
    echo -e "${RED}❌ Error: Must run from API directory or scripts directory${NC}"
    exit 1
fi

# Check for --force flag
FORCE_SEED=false
if [[ "$1" == "--force" ]]; then
    FORCE_SEED=true
    echo -e "${YELLOW}⚠️  Force mode enabled - will proceed without confirmation${NC}"
fi

# Check if database is accessible
echo -e "${BLUE}🔍 Checking database connection...${NC}"
if ! cd "$API_DIR" && uv run python -c "
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path('.') / 'src'))
from database import get_async_session

async def check_db():
    try:
        async for session in get_async_session():
            await session.execute('SELECT 1')
            print('✅ Database connection successful')
            break
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        sys.exit(1)

asyncio.run(check_db())
"; then
    echo -e "${GREEN}✅ Database connection verified${NC}"
else
    echo -e "${RED}❌ Cannot connect to database. Make sure it's running.${NC}"
    exit 1
fi

# Warning about data overwrite
if [[ "$FORCE_SEED" != "true" ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: This will add sample data to your database.${NC}"
    echo -e "${YELLOW}   Existing data will not be deleted, but new test data will be created.${NC}"
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}👋 Seeding cancelled${NC}"
        exit 0
    fi
fi

# Run the seeding script
echo -e "${BLUE}🌱 Running database seeder...${NC}"
cd "$API_DIR"

if uv run python scripts/seed_data.py; then
    echo ""
    echo -e "${GREEN}🎉 Database seeding completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo -e "   1. Start the API server: ${GREEN}uv run uvicorn src.main:app --reload${NC}"
    echo -e "   2. Start the frontend: ${GREEN}npm run dev${NC} (from frontend directory)"
    echo -e "   3. Login with the seeded credentials shown above"
    echo ""
else
    echo -e "${RED}❌ Database seeding failed${NC}"
    exit 1
fi