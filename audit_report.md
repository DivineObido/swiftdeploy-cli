# SwiftDeploy Audit Report

Generated: 2026-05-06 20:50:59 UTC

Total events recorded: 4

## Event Timeline

| Timestamp | Event | Mode | Requests | Errors | Error Rate | P99 |
|-----------|-------|------|----------|--------|------------|-----|
| 2026-05-06 20:49:07 | deploy | stable | 1.0 | 0 | 0.00% | 10ms |
| 2026-05-06 20:50:00 | promote | canary | 7.0 | 0 | 0.00% | 10ms |

## Policy Violations

### Canary Violations

Total occurrences: 2

| First seen | Last seen | Reason |
|------------|-----------|--------|
| 2026-05-06 20:50:49 | 2026-05-06 20:50:52 | P99 latency is 10000.0ms - maximum allowed is 500.0ms |
