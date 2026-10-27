"""Insurance eligibility rules.

Product spec (from the billing team):
  1. No plan on file, or no member id on file          -> NO_COVERAGE
  2. Check date is before the plan's effective_date     -> NOT_YET_ACTIVE
  3. termination_date is the LAST covered day (inclusive):
       check date after termination_date                -> TERMINATED
     termination_date of None means open-ended coverage
  4. Otherwise                                          -> ELIGIBLE
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

    if on < plan.effective_date:
        return EligibilityResult(
            EligibilityStatus.NOT_YET_ACTIVE, f"Coverage starts {plan.effective_date.isoformat()}"
        )

    if plan.termination_date is None or on >= plan.termination_date:
        return EligibilityResult(EligibilityStatus.TERMINATED, "Coverage has ended")

    return EligibilityResult(EligibilityStatus.ELIGIBLE, f"Covered by {plan.payer_name}")
