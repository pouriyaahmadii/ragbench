# Backup and Restore Runbook

**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Phase 6 deliverable

---

## Overview

This runbook covers backup and restore procedures for RAGBench local infrastructure.

### What Gets Backed Up

| Component | Volume | Backup Method | Frequency |
|-----------|--------|---------------|-----------|
| PostgreSQL | `postgres_data` | `pg_dump` (SQL) | Manual / Before changes |
| Qdrant | `qdrant_data` | Qdrant Snapshot API | Manual / Before changes |
| Redis | `redis_data` | Not typically backed up | N/A (ephemeral) |

### What Does NOT Need Backup

- Docker images (reproducible from `compose.yaml`)
- Source code (in Git)
- Configuration (in Git: `.env.example`, `compose.yaml`)
- Build artifacts (reproducible)

---

## PostgreSQL Backup

### Create Backup

```bash
# Using Makefile (recommended)
make backup-db

# Output: backups/pg_YYYY-MM-DD_HHMMSS.sql

# Or manually:
mkdir -p backups
docker compose exec postgres pg_dump -U ragbench -d ragbench > backups/pg_$(date +%F_%H%M%S).sql
```

### Backup Options

```bash
# Custom format (compressed, parallel restore)
docker compose exec postgres pg_dump -U ragbench -d ragbench -Fc > backups/pg_$(date +%F_%H%M%S).dump

# Data only (no schema)
docker compose exec postgres pg_dump -U ragbench -d ragbench --data-only > backups/pg_data_$(date +%F_%H%M%S).sql

# Specific tables only
docker compose exec postgres pg_dump -U ragbench -d ragbench -t documents -t chunks > backups/pg_core_$(date +%F_%H%M%S).sql
```

### Verify Backup

```bash
# Check file size
ls -lh backups/pg_*.sql

# Inspect first few lines
head -20 backups/pg_2026-10-22_120000.sql

# Count lines
wc -l backups/pg_2026-10-22_120000.sql
```

---

## PostgreSQL Restore

### Prerequisites

- PostgreSQL container running and healthy
- Backup file exists in `backups/`

### Restore Full Database

```bash
# Using Makefile (recommended)
make restore-db FILE=backups/pg_2026-10-22_120000.sql

# Or manually:
docker compose exec -T postgres psql -U ragbench -d ragbench < backups/pg_2026-10-22_120000.sql
```

### Restore from Custom Format

```bash
# Requires pg_restore
docker compose exec -T postgres pg_restore -U ragbench -d ragbench --clean --if-exists < backups/pg_2026-10-22_120000.dump
```

### Restore to Fresh Database (Clean Slate)

```bash
# 1. Stop services
make down-v

# 2. Start PostgreSQL only
docker compose up -d postgres

# 3. Wait for healthy
docker compose exec postgres pg_isready -U ragbench -d ragbench

# 4. Restore
make restore-db FILE=backups/pg_2026-10-22_120000.sql

# 5. Start remaining services
make up
```

### Verify Restore

```bash
# Check table counts
docker compose exec postgres psql -U ragbench -d ragbench -c "
SELECT schemaname, relname, n_live_tup
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"

# Check specific data
docker compose exec postgres psql -U ragbench -d ragbench -c "
SELECT count(*) FROM documents;
SELECT count(*) FROM chunks;
SELECT count(*) FROM index_versions;
"
```

---

## Qdrant Backup

### Create Snapshot

```bash
# Using Makefile (recommended)
make backup-qdrant

# Or manually:
curl -X POST http://127.0.0.1:6333/snapshots

# Response: {"result":{"name":"snapshot-2026-10-22-12-00-00","creation_time":"..."}}
```

### List Snapshots

```bash
curl http://127.0.0.1:6333/snapshots | jq .
```

### Download Snapshot (Optional)

```bash
# Get snapshot name first
SNAPSHOT=$(curl -s http://127.0.0.1:6333/snapshots | jq -r '.result[-1].name')

# Download
curl -O http://127.0.0.1:6333/snapshots/$SNAPSHOT
```

---

## Qdrant Restore

### Prerequisites

- Qdrant container running and healthy
- Snapshot exists (created via backup or uploaded)

### Restore from Snapshot

```bash
# Using Makefile (recommended)
make restore-qdrant SNAPSHOT=snapshot-2026-10-22-12-00-00

# Or manually:
curl -X POST http://127.0.0.1:6333/snapshots/snapshot-2026-10-22-12-00-00/recover
```

### Restore to Fresh Qdrant (Clean Slate)

```bash
# 1. Stop services
make down-v

# 2. Start Qdrant only
docker compose up -d qdrant

# 3. Wait for healthy
docker compose exec qdrant wget --spider http://localhost:6333/healthz

# 4. Restore
make restore-qdrant SNAPSHOT=snapshot-2026-10-22-12-00-00

# 5. Start remaining services
make up
```

### Verify Restore

```bash
# List collections
curl http://127.0.0.1:6333/collections | jq .

# Check collection info
curl http://127.0.0.1:6333/collections/your_collection_name | jq .

# Count points
curl -X POST http://127.0.0.1:6333/collections/your_collection_name/points/count \
  -H "Content-Type: application/json" \
  -d '{"exact": true}' | jq .
```

---

## Full Backup & Restore

### Complete Backup

```bash
# Both PostgreSQL and Qdrant
make backup-all

# Creates:
# - backups/pg_YYYY-MM-DD_HHMMSS.sql
# - Qdrant snapshot (named automatically)
```

### Complete Restore

```bash
# 1. Clean slate
make down-v

# 2. Start databases only
docker compose up -d postgres qdrant

# 3. Wait for healthy
docker compose exec postgres pg_isready -U ragbench -d ragbench
docker compose exec qdrant wget --spider http://localhost:6333/healthz

# 4. Restore PostgreSQL
make restore-db FILE=backups/pg_2026-10-22_120000.sql

# 5. Restore Qdrant
make restore-qdrant SNAPSHOT=snapshot-2026-10-22-12-00-00

# 6. Start all services
make up
```

---

## Automated Backup (Optional)

### Cron Job Example

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/ragbench && make backup-all >> /var/log/ragbench-backup.log 2>&1
```

### Backup Retention Script

```bash
#!/bin/bash
# scripts/cleanup_old_backups.sh
# Keep last 7 daily, 4 weekly, 3 monthly

BACKUP_DIR="backups"

# Daily (keep 7)
find "$BACKUP_DIR" -name "pg_*.sql" -mtime +7 -delete

# Weekly (keep 4) - Sunday backups
find "$BACKUP_DIR" -name "pg_*.sql" -mtime +28 -not -newer "$BACKUP_DIR/pg_$(date -d 'last sunday' +%F)_*.sql" -delete

# Monthly (keep 3) - 1st of month
find "$BACKUP_DIR" -name "pg_*.sql" -mtime +90 -not -name "pg_??-01_*.sql" -delete
```

---

## Disaster Recovery Scenarios

### Scenario 1: Accidental Document Deletion

```bash
# If document deleted via API but data still in volumes
# 1. Check if document exists in DB
make shell-db
# SELECT * FROM documents WHERE id = '...';

# 2. If soft-deleted, restore
# UPDATE documents SET deleted_at = NULL WHERE id = '...';

# 3. If hard-deleted, restore from backup
make restore-db FILE=backups/pg_2026-10-22_120000.sql
```

### Scenario 2: Qdrant Corruption

```bash
# Symptoms: Query errors, missing collections, incorrect results
# 1. Verify corruption
curl http://127.0.0.1:6333/collections | jq .

# 2. Restore from latest snapshot
make backup-qdrant  # Create fresh snapshot first (if possible)
make restore-qdrant SNAPSHOT=latest_snapshot_name

# 3. If no snapshot, re-index from PostgreSQL
# (Requires re-ingestion of all documents)
```

### Scenario 3: PostgreSQL Corruption

```bash
# 1. Stop services
make down

# 2. Start fresh PostgreSQL
docker compose up -d postgres

# 3. Restore from backup
make restore-db FILE=backups/pg_2026-10-22_120000.sql

# 4. Restart services
make up
```

### Scenario 4: Complete Environment Loss

```bash
# 1. Clone repository
git clone <repo-url> ragbench
cd ragbench

# 2. Configure
cp .env.example .env
# Edit .env with same POSTGRES_PASSWORD

# 3. Start databases
docker compose up -d postgres qdrant

# 4. Restore PostgreSQL
make restore-db FILE=backups/pg_2026-10-22_120000.sql

# 5. Restore Qdrant
make restore-qdrant SNAPSHOT=snapshot-2026-10-22-12-00-00

# 6. Start all
make up
```

---

## Backup Verification Checklist

Before considering a backup valid:

- [ ] Backup file exists and is non-zero size
- [ ] `pg_dump` completed without errors (check logs)
- [ ] Qdrant snapshot created successfully (API returned 200)
- [ ] Backup files stored in secure location (not just local disk)
- [ ] Restore tested in staging/isolated environment (quarterly)
- [ ] Backup timestamp documented
- [ ] Backup size reasonable (not suspiciously small/large)

---

## Storage Recommendations

### Local Development

- Store backups in `backups/` directory (gitignored)
- Copy to external drive periodically
- Use `make backup-all` before major changes

### Production (Future)

- PostgreSQL: `pg_dump` → S3/GCS with encryption
- Qdrant: Snapshots → S3/GCS with encryption
- Automated daily backups with retention policy
- Cross-region replication
- Point-in-time recovery (PITR) for PostgreSQL
- Regular restore drills (monthly)

---

## Quick Reference Card

```bash
# === BACKUP ===
make backup-db          # PostgreSQL → backups/pg_*.sql
make backup-qdrant      # Qdrant snapshot
make backup-all         # Both

# === RESTORE ===
make restore-db FILE=backups/pg_2026-10-22_120000.sql
make restore-qdrant SNAPSHOT=snapshot-2026-10-22-12-00-00

# === VERIFY ===
docker compose exec postgres psql -U ragbench -d ragbench -c "SELECT count(*) FROM documents;"
curl http://127.0.0.1:6333/collections | jq .

# === CLEAN SLATE ===
make down-v && make up
```