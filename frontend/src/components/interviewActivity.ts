import { useEffect, useRef } from "react";
import { interviewApi, type ActivityReport } from "../api";

/** Seconds without any input before you count as idle (reading counts as active up to this). */
const IDLE_AFTER = 45;
/** Idle stretches at least this long are logged on their own so the review can point at them. */
const GAP_MIN = 90;
const FLUSH_EVERY = 20;

interface Options {
  live: boolean;
  /** Interview seconds so far (pauses excluded). */
  elapsed: () => number;
  /** The side-panel tab that's showing (ticket, assistant, app, ...). */
  tab: string;
  /** The file in the focused editor pane. */
  activePath: () => string | null;
}

function emptyReport(): ActivityReport {
  return { seconds: {}, idle: 0, away: 0, keys: {}, clicks: {}, scrolls: {}, opened: [], idle_gaps: [] };
}

/**
 * Where your attention goes during a mock interview, sampled once a second: the file you're in or
 * the panel tab you're using (decided by where your last click/key/scroll/mouse move happened),
 * input counts per target, idle time, and time with the window hidden or in another app.
 * Sent to the backend in small batches and summarized in the review and for the grader.
 */
export function useActivityTracker({ live, elapsed: getElapsed, tab, activePath }: Options) {
  const elapsedRef = useRef(getElapsed);
  elapsedRef.current = getElapsed;
  const tabRef = useRef(tab);
  tabRef.current = tab;
  const pathRef = useRef(activePath);
  pathRef.current = activePath;

  useEffect(() => {
    if (!live) return;
    let report = emptyReport();
    let lastInput = Date.now();
    let region: "editor" | "panel" | "header" = "editor";
    let lastPath: string | null = null;
    let idleSince: number | null = null;
    let gapAway = false;
    let lastTick = Date.now();
    let sinceFlush = 0;
    const elapsed = () => elapsedRef.current();

    const target = () => {
      if (region === "panel") return `panel:${tabRef.current}`;
      if (region === "header") return "header";
      return `file:${pathRef.current() ?? "(none)"}`;
    };
    const bump = (counter: Record<string, number>) => {
      const t = target();
      counter[t] = (counter[t] ?? 0) + 1;
    };

    const locate = (node: EventTarget | null) => {
      const el = node instanceof Element ? node : null;
      if (el?.closest(".interview-panel")) region = "panel";
      else if (el?.closest(".interview-header")) region = "header";
      else if (el?.closest(".interview")) region = "editor";
    };
    const input = (kind: "keys" | "clicks" | "scrolls" | null) => (e: Event) => {
      locate(e.target);
      lastInput = Date.now();
      if (kind) bump(report[kind]);
    };
    const onKey = input("keys");
    const onClick = input("clicks");
    const onScroll = input("scrolls");
    const onMove = input(null);

    // The App tab is a same-origin iframe: its events don't bubble out, so listen inside it too.
    const hooked = new WeakSet<Document>();
    const hookFrames = () => {
      document.querySelectorAll<HTMLIFrameElement>(".interview-panel iframe").forEach((frame) => {
        const doc = frame.contentDocument;
        if (!doc || hooked.has(doc)) return;
        hooked.add(doc);
        const inFrame = (kind: "keys" | "clicks" | "scrolls" | null) => () => {
          region = "panel";
          lastInput = Date.now();
          if (kind) bump(report[kind]);
        };
        doc.addEventListener("keydown", inFrame("keys"), true);
        doc.addEventListener("pointerdown", inFrame("clicks"), true);
        doc.addEventListener("wheel", inFrame("scrolls"), { capture: true, passive: true });
        doc.addEventListener("mousemove", inFrame(null), { capture: true, passive: true });
      });
    };

    window.addEventListener("keydown", onKey, true);
    window.addEventListener("pointerdown", onClick, true);
    window.addEventListener("wheel", onScroll, { capture: true, passive: true });
    window.addEventListener("mousemove", onMove, { capture: true, passive: true });

    const flush = () => {
      const r = report;
      const round = (m: Record<string, number>) => Object.fromEntries(Object.entries(m).map(([k, v]) => [k, Math.round(v)]));
      r.seconds = round(r.seconds);
      r.idle = Math.round(r.idle);
      r.away = Math.round(r.away);
      report = emptyReport();
      sinceFlush = 0;
      const empty = !r.idle && !r.away && !Object.keys(r.seconds).length && !r.opened.length;
      if (!empty) void interviewApi.activity(r).catch(() => undefined);
    };

    const tick = window.setInterval(() => {
      hookFrames();
      const path = pathRef.current();
      if (path && path !== lastPath) {
        report.opened.push({ path, at: elapsed() });
        lastPath = path;
      }
      // Wall-clock delta, not +1: browsers throttle timers in hidden tabs to about once a minute.
      const now = Date.now();
      const dt = Math.min((now - lastTick) / 1000, 3600);
      lastTick = now;
      const idle = (now - lastInput) / 1000 > IDLE_AFTER;
      // Recent input means you're here even if another window has focus (e.g. reading on a second
      // monitor); otherwise a hidden tab or unfocused window is "away". hasFocus() is true in the App iframe.
      const away = document.hidden || (idle && !document.hasFocus());
      if (away) report.away += dt;
      else if (idle) report.idle += dt;
      else report.seconds[target()] = (report.seconds[target()] ?? 0) + dt;

      if (away || idle) {
        idleSince ??= away ? now - dt * 1000 : lastInput;
        gapAway ||= away;
      } else if (idleSince !== null) {
        const seconds = Math.round((now - idleSince) / 1000);
        if (seconds >= GAP_MIN) report.idle_gaps.push({ at: Math.max(0, elapsed() - seconds), seconds, away: gapAway });
        idleSince = null;
        gapAway = false;
      }
      sinceFlush += dt;
      if (sinceFlush >= FLUSH_EVERY) flush();
    }, 1000);

    const onHide = () => {
      if (document.hidden) flush();
    };
    document.addEventListener("visibilitychange", onHide);

    return () => {
      window.clearInterval(tick);
      window.removeEventListener("keydown", onKey, true);
      window.removeEventListener("pointerdown", onClick, true);
      window.removeEventListener("wheel", onScroll, true);
      window.removeEventListener("mousemove", onMove, true);
      document.removeEventListener("visibilitychange", onHide);
      flush();
    };
  }, [live]);
}
