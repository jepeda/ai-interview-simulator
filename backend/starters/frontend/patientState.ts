import type { Patient } from "./types";

/**
 * Apply a patient returned by `PATCH /patients/:id/coverage` to the list held in React state.
 *
 * Used as: setPatients((prev) => applyPatientUpdate(prev, updated))
 *
 * Requirements:
 *  - Return a NEW array (React's useState bails out of re-rendering when it gets the same reference).
 *  - Never mutate `patients` or any patient object inside it.
 *  - Replace the patient whose id matches with `updated` -- including fields that are now `null`
 *    (e.g. coverage removed: insurance_plan === null, member_id === null).
 *  - If no patient matches, return the list unchanged (a new array is fine).
 */
export function applyPatientUpdate(patients: Patient[], updated: Patient): Patient[] {
  const existing = patients.find((p) => p.id === updated.id);
  if (existing) {
    for (const [key, value] of Object.entries(updated)) {
      if (value) {
        (existing as unknown as Record<string, unknown>)[key] = value;
      }
    }
  }
  return patients;
}
