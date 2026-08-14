"""
Tests app/severity_mapping.py's conversion of this engine's numeric
Task.priority (1-10) onto the fleet's canonical Severity scale
(autonomy-events, added 2026-08-14).
"""

import pytest
from autonomy_events import Severity

from app.severity_mapping import to_canonical_severity


class TestSeverityMapping:
    @pytest.mark.parametrize(
        "priority,expected",
        [
            (1, Severity.INFO),
            (2, Severity.INFO),
            (3, Severity.LOW),
            (4, Severity.LOW),
            (5, Severity.MEDIUM),
            (6, Severity.MEDIUM),
            (7, Severity.HIGH),
            (8, Severity.HIGH),
            (9, Severity.CRITICAL),
            (10, Severity.CRITICAL),
        ],
    )
    def test_every_valid_priority_value_maps_correctly(self, priority, expected):
        assert to_canonical_severity(priority) == expected

    def test_mapping_is_monotonic(self):
        # Higher priority should never map to a lower (or equal-then-lower)
        # severity than a lower priority - catches an accidental bucket
        # boundary mistake that a table of fixed cases might not.
        from autonomy_events import severity_at_least

        results = [to_canonical_severity(p) for p in range(1, 11)]
        for lower, higher in zip(results, results[1:]):
            assert severity_at_least(higher, lower)
