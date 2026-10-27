// Mirrors the Pydantic response models in backend/workspace/clinic/schemas.py

export interface Plan {
  id: number;
  payer_name: string;
  plan_name: string;
  copay_cents: number;
  effective_date: string;
  termination_date: string | null;
}

export interface Patient {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  email: string;
  status: string | null;
  member_id: string | null;
  insurance_plan: Plan | null;
}

export interface PatientPage {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
}

export interface Eligibility {
  patient_id: number;
  status: "eligible" | "not_yet_active" | "terminated" | "no_coverage";
  reason: string;
  checked_on: string;
  plan: Plan | null;
}

export interface AppointmentRow {
  id: number;
  provider_name: string;
  starts_at: string;
  duration_minutes: number;
  status: string;
  display_time: string;
}

export interface Appointments {
  upcoming: AppointmentRow[];
  past: AppointmentRow[];
}
