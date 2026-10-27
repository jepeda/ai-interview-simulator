import type { Patient } from "./types";

/**
 * Reference solution. Fixes:
 *  - returns a new array (map), so React sees a new reference and re-renders
 *  - replaces the whole object instead of copying only truthy fields, so nulls clear old values
 *  - never mutates the previous state
 */
export function applyPatientUpdate(patients: Patient[], updated: Patient): Patient[] {
  return patients.map((p) => (p.id === updated.id ? { ...p, ...updated } : p));
}
