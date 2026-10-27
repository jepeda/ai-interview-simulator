import type { InterviewSession } from "../api";

/** mm:ss for a number of seconds (negative = overtime). */
export const clock = (seconds: number) => {
  const s = Math.abs(seconds);
  return `${seconds < 0 ? "-" : ""}${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

/** Interview seconds so far at `now` (ms): wall time since the start minus time spent paused. */
export function sessionElapsed(session: Pick<InterviewSession, "started_at" | "paused_at" | "paused_seconds">, now: number): number {
  const pausedNow = session.paused_at ? (now - new Date(session.paused_at).getTime()) / 1000 : 0;
  const seconds = (now - new Date(session.started_at).getTime()) / 1000 - (session.paused_seconds ?? 0) - pausedNow;
  return Math.max(0, Math.floor(seconds));
}
