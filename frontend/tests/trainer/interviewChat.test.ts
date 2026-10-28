import { describe, expect, it } from "vitest";
import type { InterviewEvent } from "../../src/api";
import { messagesFromEvents } from "../../src/components/InterviewChat";

const ev = (kind: InterviewEvent["kind"], extra: Record<string, unknown> = {}): InterviewEvent => ({ t: "", elapsed: 0, kind, ...extra });

describe("messagesFromEvents (chat history survives a reload)", () => {
  const events = [
    ev("start"),
    ev("prompt", { persona: "assistant", text: "Tour?" }),
    ev("reply", { persona: "assistant", text: "Here's the tour", tools: [{ name: "Read", target: "README.md" }], files_changed: [] }),
    ev("prompt", { persona: "interviewer", text: "Which timezone?" }),
    ev("reply", { persona: "interviewer", text: "The provider's." }),
    ev("note", { text: "thinking" }),
    ev("prompt", { persona: "assistant", text: "Fix it" }),
    ev("reply", { persona: "assistant", text: "", tools: [{ name: "Edit", target: "a.py" }], files_changed: ["a.py"], cancelled: true }),
  ];

  it("keeps only the persona's own conversation, in order", () => {
    expect(messagesFromEvents(events, "interviewer").map((m) => [m.role, m.text])).toEqual([
      ["user", "Which timezone?"],
      ["claude", "The provider's."],
    ]);
  });

  it("restores tools, edited files and stopped replies", () => {
    const messages = messagesFromEvents(events, "assistant");
    expect(messages).toHaveLength(4);
    expect(messages[1].tools).toEqual([{ name: "Read", target: "README.md" }]);
    expect(messages[3].filesChanged).toEqual(["a.py"]);
    expect(messages[3].meta).toBe("stopped");
  });

  it("is empty for a fresh session", () => {
    expect(messagesFromEvents([ev("start")], "assistant")).toEqual([]);
  });
});
