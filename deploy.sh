#!/bin/bash
# =============================================================================
# deploy.sh - Production Deployment Script
# 
# Dùng khi: deploy code mới có thay đổi dbt model/schema
# KHÔNG phải là startup script — đừng chạy cái này mỗi lần docker compose up
#
# Usage:
#   ./deploy.sh           → deploy bình thường (dbt run)
#   ./deploy.sh --refresh → deploy + full-refresh (khi đổi materialization)
# =============================================================================

set -e  # Dừng ngay nếu có lỗi

FULL_REFRESH=${1:-""}
DBT_CMD="dbt run --profiles-dir ."

if [ "$FULL_REFRESH" = "--refresh" ]; then
  DBT_CMD="dbt run --profiles-dir . --full-refresh"
  echo "⚠️  FULL REFRESH mode: Sẽ xóa và tạo lại toàn bộ dbt models"
fi

echo "======================================================"
echo "🚀 Starting deployment..."
echo "======================================================"

# Bước 1: Build và khởi động infrastructure
echo ""
echo "📦 Step 1: Starting infrastructure..."
docker compose up -d --build

# Bước 2: Đợi PostgreSQL sẵn sàng
echo ""
echo "⏳ Step 2: Waiting for database to be ready..."
until docker exec warehouse_postgres pg_isready -U "${DB_USER:-postgres}" > /dev/null 2>&1; do
  echo "   Database not ready yet, retrying in 3s..."
  sleep 3
done
echo "   ✅ Database is ready!"

# Bước 3: Chạy dbt trong container Airflow
echo ""
echo "🔄 Step 3: Running dbt transformation ($DBT_CMD)..."
docker exec airflow_orchestrator bash -c "cd /app/analytics/dbt && $DBT_CMD"

echo ""
echo "======================================================"
echo "✅ Deployment complete!"
echo "   Airflow UI: http://localhost:8080"
echo "   Metabase:   http://localhost:3000"
echo "======================================================"
