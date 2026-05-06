package canary

import rego.v1

#  Allow if nothing is denied
allow := count(deny) == 0

# Deny Rules

# Deny if error rate is above the threshold
# error_rate is a percentage e.g 1.5 means 1.5%
deny contains msg if {
    input.error_rate > data.canary.thresholds.max_error_rate_percent
    msg := sprintf(
        "Error rate is %.2f%% — maximum allowed is %.2f%%",
        [input.error_rate, data.canary.thresholds.max_error_rate_percent]
    )
}

# Deny if P99 latency is above the threshold
# p99_latency_ms is in milliseconds e.g 250.5 means 250.5ms
deny contains msg if {
    input.p99_latency_ms > data.canary.thresholds.max_p99_latency_ms
    msg := sprintf(
        "P99 latency is %.1fms — maximum allowed is %.1fms",
        [input.p99_latency_ms, data.canary.thresholds.max_p99_latency_ms]
    )
}
