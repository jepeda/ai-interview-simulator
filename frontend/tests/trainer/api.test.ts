import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { generateApi, interviewApi, setInterviewScenario, trainerApi } from "../../src/api";

type Call = { url: string; init: RequestInit };
let calls: Call[];

beforeEach(() => {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit = {}) => {
      calls.push({ url, init });
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "Content-Type": "application/json" } });
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  setInterviewScenario(null);
});

const header = (c: Call, name: string) => (c.init.headers as Record<string, string> | undefined)?.[name];

describe("the scenario header (keeps the sandbox in its own session slot)", () => {
  it("is sent with interview calls once a scenario is on screen", async () => {
    setInterviewScenario("ai0");
    await interviewApi.run();
    await interviewApi.note("hello", "typed");
    expect(calls.map((c) => header(c, "X-Interview-Scenario"))).toEqual(["ai0", "ai0"]);
  });

  it("is not sent with other API calls", async () => {
    setInterviewScenario("ai0");
    await trainerApi.meta();
    await generateApi.jobs();
    expect(calls.every((c) => header(c, "X-Interview-Scenario") === undefined)).toBe(true);
  });

  it("is not sent when no scenario is set", async () => {
    await interviewApi.run();
    expect(header(calls[0], "X-Interview-Scenario")).toBeUndefined();
  });
});

describe("request shapes", () => {
  it("starts an interview for a scenario", async () => {
    await interviewApi.start("ai4", true);
    expect(calls[0].url).toBe("/api/interview/start");
    expect(calls[0].init.method).toBe("POST");
    expect(JSON.parse(calls[0].init.body as string)).toEqual({ scenario: "ai4", reset_code: true });
  });

  it("asks for a scenario's view by query string", async () => {
    await interviewApi.get("ai 1");
    expect(calls[0].url).toBe("/api/interview?scenario=ai%201");
  });

  it("saves and clears the interview date", async () => {
    await trainerApi.saveInterviewDate("2026-11-03");
    await trainerApi.saveInterviewDate(null);
    expect(calls.map((c) => [c.init.method, JSON.parse(c.init.body as string)])).toEqual([
      ["PUT", { interview_date: "2026-11-03" }],
      ["PUT", { interview_date: null }],
    ]);
  });

  it("generates and deletes scenarios", async () => {
    await generateApi.start({ company: "Acme", domain: "", minutes: 30, difficulty: "warmup" });
    await generateApi.deleteScenario("gen_acme");
    expect(calls[0].url).toBe("/api/generate");
    expect(JSON.parse(calls[0].init.body as string)).toEqual({ company: "Acme", domain: "", minutes: 30, difficulty: "warmup" });
    expect([calls[1].url, calls[1].init.method]).toEqual(["/api/generate/scenario/gen_acme", "DELETE"]);
  });

  it("turns an error response into a readable error", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("The interview is paused", { status: 409, statusText: "Conflict" })));
    await expect(interviewApi.run()).rejects.toThrow("409 Conflict: The interview is paused");
  });
});
