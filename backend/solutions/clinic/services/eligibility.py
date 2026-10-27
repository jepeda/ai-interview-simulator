"""Insurance eligibility rules (reference solution).

Fixes:
  - missing member id now counts as NO_COVERAGE (rule 1 was only half implemented)
  - open-ended plans (termination_date None) are ELIGIBLE, not TERMINATED
  - the termination date itself is still covered (inclusive): `>` not `>=`
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from clinic.models import InsurancePlan


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    NOT_YET_ACTIVE = "not_yet_active"
    TERMINATED = "terminated"
    NO_COVERAGE = "no_coverage"


@dataclass(frozen=True)
class EligibilityResult:
    status: EligibilityStatus
    reason: str


def check_eligibility(
    plan: InsurancePlan | None, member_id: str | None, on: date
) -> EligibilityResult:
    if plan is None:
        return EligibilityResult(EligibilityStatus.NO_COVERAGE, "No insurance plan on file")
    if not member_id:
        return EligibilityResult(EligibilityStatus.NO_COVERAGE, "No member id on file")

    if on < plan.effective_date:
        return EligibilityResult(
            EligibilityStatus.NOT_YET_ACTIVE, f"Coverage starts {plan.effective_date.isoformat()}"
        )

    if plan.termination_date is not None and on > plan.termination_date:
        return EligibilityResult(EligibilityStatus.TERMINATED, "Coverage has ended")

    return EligibilityResult(EligibilityStatus.ELIGIBLE, f"Covered by {plan.payer_name}")
