import { describe, expect, it } from "vitest";
import { endpointsOf, exampleValue, type Spec } from "../../src/components/ApiTester";

// A trimmed version of what FastAPI generates for the booking service.
const spec: Spec = {
  paths: {
    "/providers/search": {
      get: {
        summary: "Search",
        parameters: [
          { name: "state", in: "query", required: true, schema: { type: "string" } },
          { name: "page", in: "query", required: false, schema: { type: "integer", default: 1 } },
        ],
      },
    },
    "/providers/{provider_id}/slots": {
      get: {
        summary: "Get Slots",
        parameters: [
          { name: "provider_id", in: "path", required: true, schema: { type: "integer" } },
          { name: "date", in: "query", required: true, schema: { type: "string", format: "date" } },
        ],
      },
    },
    "/appointments": {
      post: {
        summary: "Create Appointment",
        requestBody: { content: { "application/json": { schema: { $ref: "#/components/schemas/BookingRequest" } } } },
      },
    },
  },
  components: {
    schemas: {
      BookingRequest: {
        type: "object",
        properties: {
          provider_id: { type: "integer" },
          starts_at: { type: "string", format: "date-time" },
          idempotency_key: { anyOf: [{ type: "string" }, { type: "null" }] },
          cancelled_by: { type: "string", enum: ["patient", "provider"] },
          tags: { type: "array", items: { type: "string" } },
          urgent: { type: "boolean" },
        },
      },
    },
  },
};

describe("endpointsOf", () => {
  const endpoints = endpointsOf(spec);

  it("lists every operation with its method and summary", () => {
    expect(endpoints.map((e) => `${e.method} ${e.path}`)).toEqual([
      "GET /providers/search",
      "GET /providers/{provider_id}/slots",
      "POST /appointments",
    ]);
    expect(endpoints[2].summary).toBe("Create Appointment");
  });

  it("pre-fills only the required query parameters and keeps path params as placeholders", () => {
    expect(endpoints[0].url).toBe("/providers/search?state=string");
    expect(endpoints[1].url).toBe("/providers/{provider_id}/slots?date=2026-11-02");
  });

  it("builds an example JSON body from the request schema", () => {
    expect(endpoints[0].body).toBe("");
    const body = JSON.parse(endpoints[2].body) as Record<string, unknown>;
    expect(body.provider_id).toBe(1);
    expect(body.starts_at).toBe("2026-11-02T09:00:00-05:00");
    expect(body.idempotency_key).toMatch(/^key-[a-z0-9]+$/);
    expect(body.cancelled_by).toBe("patient");
    expect(body.tags).toEqual(["string"]);
    expect(body.urgent).toBe(true);
  });
});

describe("exampleValue", () => {
  it("prefers explicit examples and defaults", () => {
    expect(exampleValue({ type: "integer", example: 42 }, spec)).toBe(42);
    expect(exampleValue({ type: "integer", default: 7 }, spec)).toBe(7);
  });

  it("stops on self-referencing schemas instead of looping forever", () => {
    const loop: Spec = { paths: {}, components: { schemas: { Node: { type: "object", properties: { child: { $ref: "#/components/schemas/Node" } } } } } };
    expect(() => exampleValue({ $ref: "#/components/schemas/Node" }, loop)).not.toThrow();
  });

  it("returns null for unknown shapes", () => {
    expect(exampleValue(undefined, spec)).toBeNull();
    expect(exampleValue({}, spec)).toBeNull();
  });
});
