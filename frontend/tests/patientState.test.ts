import { describe, expect, it } from "vitest";
import { applyPatientUpdate } from "@clinic/patientState";
import type { Patient, Plan } from "../src/clinic/types";

const aetna: Plan = {
  id: 1,
  payer_name: "Aetna",
  plan_name: "Choice POS II",
  copay_cents: 2500,
  effective_date: "2024-01-01",
  termination_date: null,
};
const cigna: Plan = { ...aetna, id: 2, payer_name: "Cigna", plan_name: "Open Access Plus" };

function patient(id: number, overrides: Partial<Patient> = {}): Patient {
  return {
    id,
    first_name: `First${id}`,
    last_name: `Last${id}`,
    date_of_birth: "1990-01-01",
    email: `p${id}@example.com`,
    status: "active",
    member_id: "W1",
    insurance_plan: aetna,
    ...overrides,
  };
}

/** Freeze the list and every patient: any mutation throws a TypeError (ES modules are strict). */
function frozenList(): Patient[] {
  return Object.freeze([Object.freeze(patient(1)), Object.freeze(patient(2))]) as Patient[];
}

describe("applyPatientUpdate", () => {
  it("returns a new array so React re-renders", () => {
    const prev = [patient(1), patient(2)];
    const next = applyPatientUpdate(prev, patient(2, { insurance_plan: cigna }));
    expect(next).not.toBe(prev);
  });

  it("replaces the matching patient with the updated data", () => {
    const next = applyPatientUpdate([patient(1), patient(2)], patient(2, { insurance_plan: cigna, member_id: "C-777" }));
    expect(next[1].insurance_plan?.payer_name).toBe("Cigna");
    expect(next[1].member_id).toBe("C-777");
  });

  it("does not mutate the previous state", () => {
    const prev = frozenList();
    expect(() => applyPatientUpdate(prev, patient(2, { insurance_plan: cigna }))).not.toThrow();
    expect(prev[1].insurance_plan?.payer_name).toBe("Aetna");
  });

  it("applies null fields (coverage removed)", () => {
    const next = applyPatientUpdate([patient(1), patient(2)], patient(2, { insurance_plan: null, member_id: null }));
    expect(next[1].insurance_plan).toBeNull();
    expect(next[1].member_id).toBeNull();
  });

  it("keeps the other patients untouched (same object references)", () => {
    const prev = [patient(1), patient(2), patient(3)];
    const next = applyPatientUpdate(prev, patient(2, { insurance_plan: cigna }));
    expect(next).toHaveLength(3);
    expect(next[0]).toBe(prev[0]);
    expect(next[2]).toBe(prev[2]);
  });

  it("leaves the list as-is when no patient matches", () => {
    const prev = [patient(1)];
    expect(applyPatientUpdate(prev, patient(99))).toEqual(prev);
  });
});
