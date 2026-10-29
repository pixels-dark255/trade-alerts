function assertEquals(a: unknown, b: unknown) { const x = JSON.stringify(a), y = JSON.stringify(b); if (x !== y) throw new Error(`expected ${y} got ${x}`); }
import { handler, hmacHex, payerEmail, planFor } from "./index.ts";

Deno.test("plan mapping", () => {
  assertEquals(planFor(29900), ["pro", 30]);
  assertEquals(planFor(1999900), ["firm", 365]);
  assertEquals(planFor(100), null);
});
Deno.test("email from notes first", () => {
  assertEquals(payerEmail({ email: "card@x.in", notes: { email_used_for_sagarlekh_signup: "Me@Firm.in" } }), "me@firm.in");
  assertEquals(payerEmail({ email: "a@b.in", notes: {} }), "a@b.in");
});
Deno.test("webhook flow", async () => {
  Deno.env.set("RAZORPAY_WEBHOOK_SECRET", "s3cret"); Deno.env.set("SUPABASE_URL", "https://db.test");
  Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "k"); Deno.env.set("RESEND_API_KEY", "r"); Deno.env.set("OWNER_EMAIL", "o@x.in");
  const calls: { url: string; body: any }[] = [];
  globalThis.fetch = (async (url: string, init: any) => {
    calls.push({ url, body: JSON.parse(init.body) });
    if (url.includes("apply_payment")) return new Response(JSON.stringify({ status: "created", paid_until: "2026-11-28", token: "tok-1" }));
    return new Response("{}");
  }) as typeof fetch;
  const body = JSON.stringify({ event: "payment.captured", payload: { payment: { entity:
    { id: "pay_9", amount: 199900, status: "captured", email: "a@b.in", notes: { email: "cha@firm.in" } } } } });
  const bad = await handler(new Request("https://f", { method: "POST", body, headers: { "x-razorpay-signature": "nope" } }));
  assertEquals(bad.status, 401);
  const ok = await handler(new Request("https://f", { method: "POST", body,
    headers: { "x-razorpay-signature": await hmacHex("s3cret", body) } }));
  assertEquals(await ok.text(), "applied");
  assertEquals(calls[0].body, { p_payment_id: "pay_9", p_email: "cha@firm.in", p_plan: "firm", p_days: 30, p_amount: 1999 });
  assertEquals(calls[1].body.to, ["cha@firm.in"]);
  assertEquals(String(calls[1].body.html).includes("clients.html?t=tok-1"), true);
  assertEquals(calls[2].body.to, ["o@x.in"]);
  calls.length = 0;
  const odd = JSON.stringify({ event: "payment.captured", payload: { payment: { entity: { id: "pay_10", amount: 50000, status: "captured", email: "z@z.in" } } } });
  const r3 = await handler(new Request("https://f", { method: "POST", body: odd, headers: { "x-razorpay-signature": await hmacHex("s3cret", odd) } }));
  assertEquals(await r3.text(), "unmatched, owner notified");
  assertEquals(calls.length, 1);
});
