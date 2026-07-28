# Backup and Restore Runbook

목표는 RPO 24시간, RTO 4시간입니다. PostgreSQL backup은 age로 암호화하고 SHA-256
checksum 및 30일 보존 metadata와 함께 저장합니다.

## Backup

```sh
export DATABASE_URL='postgresql://backup-user:***@db/ott_feed'
export BACKUP_REMOTE='s3:bucket/ott-feed'
export BACKUP_AGE_RECIPIENT_FILE='/run/secrets/backup_age_recipient'
sh scripts/backup.sh
```

U02 export artifact 저장소는 PostgreSQL backup 및 일반 object backup에서 제외합니다.
Export는 최대 24시간의 일회성 사용자 전달물이며 restore로 되살리면 안 됩니다. Backup
manifest에는 database checksum, migration revision, key-version 분포와 export exclusion을
기록합니다. Backup 파일에 KEK, session pepper, blind-index key 또는 export key를 포함하지
않습니다. Key backup은 분리된 관리형 key escrow 정책을 따릅니다.

## 격리 Restore 검증

```sh
export RESTORE_ARCHIVE='/secure/ott-feed-....tar.gz.age'
export RESTORE_CHECKSUM='manifest-sha256'
export RESTORE_AGE_IDENTITY_FILE='/run/secrets/backup_age_identity'
export RESTORE_DATABASE_URL='postgresql://restore-user:***@isolated-db/ott_feed_restore'
export RESTORE_SMOKE_COMMAND='python3 scripts/synthetic.py http://isolated-api:8000'
sh scripts/restore.sh
```

Restore 대상은 반드시 운영과 분리된 빈 데이터베이스여야 합니다. 검증 순서는 checksum,
decrypt, globals/schema/data restore, Alembic revision, U02 encrypted-field decrypt sample,
identity smoke, closure 재진입 순서입니다.

## U02 재진입 불변식

Restore 후 트래픽을 열기 전에 다음을 수행합니다.

1. `deletion_pending` 계정은 로그인 불가 상태인지 확인하고 미완료 category를 재등록합니다.
2. withdrawn consent의 source event와 derived feature가 남아 있으면 high-lane cleanup을
   재등록하며 그동안 personalization을 fail closed 처리합니다.
3. key rotation checkpoint를 현재 row와 대조하고 새 key 쓰기를 유지한 채 재개합니다.
4. 만료되었거나 consumed된 export metadata와 모든 restore된 export reference를 폐기합니다.
5. session은 운영 전환 시 전체 revoke하거나 별도 승인된 recovery 정책을 적용합니다.

분기별로 격리 restore를 실행하고 소요 시간, checksum, revision, closure 결과 및 담당자
승인을 보존합니다.

## U03 Rebuildable Data

Back up approved catalog revisions, current approval state, sources, verified availability, active-generation pointers, projection receipts/gaps and search quality evidence. Feed/text/vector projection rows and embeddings are rebuildable and may be excluded when recovery-time objectives permit. After restore, replay from the last contiguous CatalogVersion, rebuild immutable candidates, rerun the quality gate and atomically activate them.

## U04 Restore Re-entry

Keep provider claims disabled after restore. Verify that every job references an existing provider-policy version, every decision references an immutable rule version, cursors never regress, publication receipts remain unique and quarantined records cannot appear in publication work. Reconcile every pending publication key with U03 before enabling provider claims. Expired raw bodies may remain expired, but their permitted digest, provenance and decision lineage must still be present. Enable publication first; enable provider claims only after reconciliation reports zero unknown outcomes.
