package infrastructure

import rego.v1

# Allow if nothing is denied
# The CLI checks this field. If deny is empty, allow is true.

default allow := false

allow := true if {
    count(deny) == 0
}

#  Deny Rules 

# Deny if disk free space is below the threshold
deny contains msg if {
    input.disk_free_gb < data.infrastructure.thresholds.min_disk_free_gb
    msg := sprintf(
        "Disk free space is %.1fGB — minimum required is %.1fGB",
        [input.disk_free_gb, data.infrastructure.thresholds.min_disk_free_gb]
    )
}

# Deny if CPU load is above the threshold
deny contains msg if {
    input.cpu_load > data.infrastructure.thresholds.max_cpu_load
    msg := sprintf(
        "CPU load is %.2f — maximum allowed is %.2f",
        [input.cpu_load, data.infrastructure.thresholds.max_cpu_load]
    )
}

# Deny if memory free is below the threshold
deny contains msg if {
    input.memory_free_percent < data.infrastructure.thresholds.min_memory_free_percent
    msg := sprintf(
        "Memory free is %.1f%% — minimum required is %.1f%%",
        [input.memory_free_percent, data.infrastructure.thresholds.min_memory_free_percent]
    )
}