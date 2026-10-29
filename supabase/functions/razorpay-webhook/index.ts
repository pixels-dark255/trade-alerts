// Razorpay → Sagarlekh: switches on the paid plan automatically when a payment is captured.
// Deploy: Supabase Dashboard → Edge Functions → "razorpay-webhook" (Verify JWT: OFF). Secrets below.
// Secrets: RAZORPAY_WEBHOOK_SECRET (same text as in Razorpay → Webhooks), RESEND_API_KEY, MAIL_FROM, OWNER_EMAIL,
//          SITE_URL (https://alerts.dharalabs.in), optional PLAN_MAP (JSON, see DEFAULT_PLAN_MAP).
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase automatically.

// amount in rupees -> [plan, days]. Update via the PLAN_MAP secret when prices change (no code change needed).
export const DEFAULT_PLAN_MAP: Record<string, [string, number]> = {
  "299": ["pro", 30], "2999": ["pro", 365], "1999": ["firm", 30], "19999": ["firm", 365],
};

const env = (k: string, d = "") => (Deno.env.get(k) ?? d).trim();

export async function hmacHex(secret: string, body: string): Promise<string> {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

export function payerEmail(p: Record<string, any>): string {
  const notes = (p.notes && typeof p.notes === "object") ? p.notes as Record<string, string> : {};
  const fromNotes = Object.entries(notes).sort(([a], [b]) => Number(!/email/i.test(a)) - Number(!/email/i.test(b)))
    .map(([, v]) => String(v ?? "").trim()).find((v) => /^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(v));
  const direct = String(p.email ?? "").trim();
  // the "Email used for Sagarlekh signup" field may be stored in notes; prefer it over the checkout email
  return (fromNotes || direct).toLowerCase();
}

export function planFor(amountPaise: number, map = DEFAULT_PLAN_MAP): [string, number] | null {
  const rupees = String(Math.round(amountPaise / 100));
  return map[rupees] ?? null;
}

async function sendMail(to: string, subject: string, html: string) {
  const key = env("RESEND_API_KEY");
  if (!key || !to) return;
  await fetch("https://api.resend.com/emails", {
    method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: env("MAIL_FROM"), to: [to], subject, html, reply_to: env("CONTACT_EMAIL", "dharalabs.co@gmail.com") }),
  });
}

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));

export async function handler(req: Request): Promise<Response> {
  if (req.method !== "POST") return new Response("ok");
  const body = await req.text();
  const secret = env("RAZORPAY_WEBHOOK_SECRET");
  const given = req.headers.get("x-razorpay-signature") ?? "";
  if (!secret || !safeEqual(await hmacHex(secret, body), given)) return new Response("bad signature", { status: 401 });

  let evt: any;
  try { evt = JSON.parse(body); } catch { return new Response("bad json", { status: 400 }); }
  const p = evt?.payload?.payment?.entity;
  if (evt?.event !== "payment.captured" || !p || p.status !== "captured") return new Response("ignored");

  let map = DEFAULT_PLAN_MAP;
  try { if (env("PLAN_MAP")) map = JSON.parse(env("PLAN_MAP")); } catch { /* keep default */ }
  const plan = planFor(Number(p.amount), map);
  const email = payerEmail(p);
  const owner = env("OWNER_EMAIL");
  if (!plan || !email) {
    await sendMail(owner, "[Sagarlekh] Payment needs you",
      `<p>Payment ${esc(String(p.id))} of Rs ${Number(p.amount) / 100} could not be matched automatically ` +
      `(${!plan ? "unknown amount" : "no email"}). Please upgrade by hand in Supabase.</p>`);
    return new Response("unmatched, owner notified");
  }

  const r = await fetch(`${env("SUPABASE_URL")}/rest/v1/rpc/apply_payment`, {
    method: "POST",
    headers: { apikey: env("SUPABASE_SERVICE_ROLE_KEY"), Authorization: `Bearer ${env("SUPABASE_SERVICE_ROLE_KEY")}`,
               "Content-Type": "application/json" },
    body: JSON.stringify({ p_payment_id: String(p.id), p_email: email, p_plan: plan[0], p_days: plan[1],
                           p_amount: Number(p.amount) / 100 }),
  });
  if (!r.ok) return new Response("db error", { status: 500 });          // Razorpay retries later
  const res = await r.json();
  if (res.status === "duplicate") return new Response("already applied");

  const site = env("SITE_URL", "https://alerts.dharalabs.in").replace(/\/$/, "");
  const name = plan[0] === "firm" ? "Firm" : "Pro";
  const clients = plan[0] === "firm"
    ? `<p><b>Next step:</b> add your clients and their products here (up to 25):<br>` +
      `<a href="${site}/clients.html?t=${res.token}">${site}/clients.html</a><br>Keep this link private; it works like a password.</p>`
    : `<p>Want to change your products or HS codes? Just reply to this email.</p>`;
  await sendMail(email, `Your Sagarlekh ${name} plan is active`,
    `<div style="font-family:Arial,sans-serif;max-width:620px;margin:auto"><h2>Sagarlekh</h2><p>Namaste,</p>` +
    `<p>Thank you. We received Rs ${Number(p.amount) / 100} and your <b>${name}</b> plan is active until ` +
    `<b>${esc(String(res.paid_until))}</b>. You will get an email the same day a DGFT notice touches your codes.</p>${clients}` +
    `<p style="font-size:13px;color:#555">Plans never renew automatically; we email you before yours ends. ` +
    `7-day refund on your first payment: ${site}/refund.html</p></div>`);
  await sendMail(owner, `[Sagarlekh] PAID: ${name} Rs ${Number(p.amount) / 100}`,
    `<p>${esc(email)} paid Rs ${Number(p.amount) / 100} (${esc(String(p.id))}). ${name} active until ${esc(String(res.paid_until))} (${res.status}).</p>`);
  return new Response("applied");
}

if (import.meta.main) Deno.serve(handler);
