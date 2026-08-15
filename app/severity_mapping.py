"""
Maps this engine's raw numeric Task.priority (1-10) onto the fleet's
canonical Severity scale (autonomy-events, added 2026-08-14 - see its
severity/__init__.py for the full story of why a canonical scale exists).

Deliberately doesn't replace the numeric field - it's genuinely useful
for scheduling math (sorting, weighting) in a way a 5-value category
isn't. This mapping exists only for the boundary where a scheduling
situation needs to be compared against severities reported by other
engines (e.g. a DLQRemediationConsumer decision, or a monitoring rollup)
that don't know what "priority 7" means but do understand Severity.HIGH.

Bucketed evenly across the real 1-10 range used by Task.priority (see
app/schemas/task_schemas.py) into 5 pairs, extending - not contradicting
- dependency_scheduler.py's existing 3-tier bucketing (>=8 high_priority,
>=5 normal, else low_priority): 8-10 here is HIGH/CRITICAL, 5-7 is
MEDIUM/HIGH, <5 is INFO/LOW, same rough shape with more resolution.
"""

from autonomy_events import Severity


def to_canonical_severity(priority: int) -> Severity:
    """Convert a Task.priority value (1-10) to the fleet's canonical Severity."""
    if priority <= 2:
        return Severity.INFO
    if priority <= 4:
        return Severity.LOW
    if priority <= 6:
        return Severity.MEDIUM
    if priority <= 8:
        return Severity.HIGH
    return Severity.CRITICAL
