// Calcitax website Worker.
// Static pages are served from ./public by Workers Static Assets.
// This script only runs for requests that don't match a static file,
// and handles POST /api/contact by emailing the message to the firm's inbox.

import { EmailMessage } from "cloudflare:email";

const FROM_ADDRESS = "website@calcitax.com";
const TO_ADDRESS = "calcitax@gmail.com";

const SERVICES = new Set([
  "Personal tax return (T1)",
  "Self-employed or rental income",
  "Corporate tax return (T2)",
  "Bookkeeping",
  "Payroll",
  "GST/HST or PST",
  "Newcomer to Canada",
  "CRA letter or late returns",
  "Something else",
]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/contact") {
      if (request.method !== "POST") {
        return json({ ok: false, error: "Method not allowed" }, 405);
      }
      return handleContact(request, env);
    }

    if (url.pathname === "/api/t1-intake" || url.pathname === "/api/t2-intake") {
      if (request.method !== "POST") {
        return json({ ok: false, error: "Method not allowed" }, 405);
      }
      return handleIntake(request, env, url.pathname === "/api/t2-intake" ? "t2" : "t1");
    }

    // Anything else that isn't a static file: serve the 404 page.
    const page = await env.ASSETS.fetch(new Request(new URL("/404.html", url)));
    return new Response(page.body, { status: 404, headers: page.headers });
  },
};

async function handleContact(request, env) {
  let data;
  try {
    const type = request.headers.get("content-type") || "";
    if (type.includes("application/json")) {
      data = await request.json();
    } else {
      data = Object.fromEntries(await request.formData());
    }
  } catch {
    return json({ ok: false, error: "Invalid request" }, 400);
  }

  // Honeypot: real visitors never fill this hidden field; bots often do.
  if (clean(data.website)) {
    return json({ ok: true });
  }

  const name = oneLine(data.name).slice(0, 100);
  const email = oneLine(data.email).slice(0, 200);
  const service = SERVICES.has(oneLine(data.service)) ? oneLine(data.service) : "Something else";
  const message = clean(data.message).slice(0, 5000);

  if (!name || !isEmail(email)) {
    return json({ ok: false, error: "Please enter your name and a valid email address." }, 400);
  }

  const body = [
    "New message from the calcitax.com contact form",
    "",
    `Name:    ${name}`,
    `Email:   ${email}`,
    `Service: ${service}`,
    "",
    "Message:",
    message || "(no message)",
    "",
    "Reply to this email to answer the client directly.",
  ].join("\r\n");

  const raw = [
    `From: Calcitax Website <${FROM_ADDRESS}>`,
    `To: ${TO_ADDRESS}`,
    `Reply-To: ${email}`,
    `Subject: ${encodeHeader(`Website enquiry: ${service} - ${name}`)}`,
    `Date: ${new Date().toUTCString()}`,
    `Message-ID: <${crypto.randomUUID()}@calcitax.com>`,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    wrap(base64(body)),
  ].join("\r\n");

  try {
    await env.CONTACT_EMAIL.send(new EmailMessage(FROM_ADDRESS, TO_ADDRESS, raw));
  } catch (err) {
    console.error("Contact form email failed:", err && err.message);
    return json({ ok: false, error: "Sorry, your message couldn't be sent. Please email info@calcitax.com." }, 502);
  }

  return json({ ok: true });
}

// ---------------------------------------------------------------------------
// Client information forms (T1 personal, T2 corporate)
// ---------------------------------------------------------------------------

const MAX_BODY_BYTES = 200_000;

async function handleIntake(request, env, kind) {
  let data;
  try {
    const text = await request.text();
    if (text.length > MAX_BODY_BYTES) {
      return json({ ok: false, error: "Your form is too long to send. Please shorten the notes and try again." }, 413);
    }
    data = JSON.parse(text);
  } catch {
    return json({ ok: false, error: "Invalid request" }, 400);
  }
  if (!data || typeof data !== "object") return json({ ok: false, error: "Invalid request" }, 400);

  if (clean(data.website)) return json({ ok: true }); // honeypot

  const firstName = oneLine(data.firstName).slice(0, 80);
  const lastName = oneLine(data.lastName).slice(0, 80);
  const email = oneLine(data.email).slice(0, 200);
  const phone = oneLine(data.phone).slice(0, 40);
  const company = oneLine(data.company).slice(0, 150);
  if (kind === "t2" && !company) {
    return json({ ok: false, error: "Please fill in the corporation's legal name." }, 400);
  }
  if (!firstName || !lastName || !isEmail(email)) {
    return json({ ok: false, error: "Please fill in your first name, last name and a valid email address." }, 400);
  }

  const applies = (Array.isArray(data.applies) ? data.applies : [])
    .slice(0, 20).map((a) => oneLine(a).slice(0, 80)).filter(Boolean);
  const sections = sanitizeSections(data.sections);

  const name = `${firstName} ${lastName}`;
  const intake = {
    kind,
    name,
    company,
    title: kind === "t2" ? `T2 for ${company}` : `T1 for ${name}`,
    subtitle: kind === "t2" ? "Corporate tax return and year-end" : "2026 personal tax return",
    email,
    phone,
    applies,
    sections,
    submitted: new Date().toLocaleString("en-CA", {
      timeZone: "America/Vancouver", dateStyle: "medium", timeStyle: "short",
    }) + " (Pacific)",
  };

  const subject = kind === "t2"
    ? `T2 client form: ${company} (contact: ${name})`
    : `T1 client form: ${name} (2026 tax year)`;
  const raw = buildMultipartEmail({
    replyTo: email,
    subject,
    text: renderIntakeText(intake),
    html: renderIntakeHtml(intake),
  });

  try {
    await env.CONTACT_EMAIL.send(new EmailMessage(FROM_ADDRESS, TO_ADDRESS, raw));
  } catch (err) {
    console.error(`${kind.toUpperCase()} intake email failed:`, err && err.message);
    return json({ ok: false, error: "Sorry, your form couldn't be sent. Please try again, or email info@calcitax.com." }, 502);
  }
  return json({ ok: true });
}

function sanitizeSections(input) {
  const out = [];
  if (!Array.isArray(input)) return out;
  for (const s of input.slice(0, 25)) {
    if (!s || typeof s !== "object") continue;
    const title = oneLine(s.title).slice(0, 100);
    const items = [];
    for (const it of (Array.isArray(s.items) ? s.items : []).slice(0, 150)) {
      if (!it || typeof it !== "object") continue;
      if (typeof it.heading === "string") {
        const heading = oneLine(it.heading).slice(0, 100);
        if (heading) items.push({ heading });
        continue;
      }
      const rows = (Array.isArray(it.rows) ? it.rows : []).slice(0, 60)
        .map((r) => ({
          label: oneLine(r && r.label).slice(0, 200),
          value: clean(r && r.value).slice(0, 3000),
        }))
        .filter((r) => r.label && r.value);
      if (!rows.length) continue;
      const group = typeof it.group === "string" ? oneLine(it.group).slice(0, 100) : "";
      items.push(group ? { group, rows } : { rows });
    }
    if (title && items.some((i) => i.rows)) out.push({ title, items });
  }
  return out;
}

function renderIntakeText(d) {
  const heading = d.kind === "t2" ? "NEW T2 CORPORATE CLIENT FORM" : "NEW T1 CLIENT FORM (2026 tax year)";
  const lines = [
    heading,
    "=".repeat(heading.length),
    "",
    ...(d.company ? [`Company:   ${d.company}`] : []),
    `${d.company ? "Contact:  " : "Client:   "} ${d.name}`,
    `Email:     ${d.email}`,
    `Phone:     ${d.phone || "-"}`,
    `Submitted: ${d.submitted}`,
    `Applies:   ${d.applies.length ? d.applies.join(", ") : "-"}`,
  ];
  for (const s of d.sections) {
    lines.push("", "", s.title.toUpperCase(), "-".repeat(s.title.length));
    for (const it of s.items) {
      if (it.heading) { lines.push("", `[${it.heading}]`); continue; }
      if (it.group) lines.push("", `${it.group}:`);
      for (const r of it.rows) {
        const value = r.value.replace(/\r?\n/g, "\n      ");
        lines.push(`${it.group ? "  " : ""}- ${r.label}: ${value}`);
      }
    }
  }
  lines.push("", "", "Reply to this email to contact the client directly.");
  return lines.join("\r\n");
}

function renderIntakeHtml(d) {
  const font = "font-family:Arial,Helvetica,sans-serif;";
  const rowHtml = (r) =>
    `<tr><td style="${font}padding:9px 14px;border-bottom:1px solid #E3E8EE;color:#4A5568;font-size:14px;width:46%;vertical-align:top">${esc(r.label)}</td>` +
    `<td style="${font}padding:9px 14px;border-bottom:1px solid #E3E8EE;color:#0F1B2D;font-size:14px;font-weight:bold;vertical-align:top">${esc(r.value).replace(/\r?\n/g, "<br>")}</td></tr>`;

  let body = "";
  for (const s of d.sections) {
    body += `<tr><td style="padding:28px 0 8px"><div style="${font}font-size:18px;font-weight:bold;color:#0B6E5F">${esc(s.title)}</div></td></tr>`;
    body += `<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E3E8EE;border-radius:8px;border-collapse:separate;overflow:hidden">`;
    for (const it of s.items) {
      if (it.heading) {
        body += `<tr><td colspan="2" style="${font}padding:10px 14px;background:#F4F7F6;font-size:13px;font-weight:bold;color:#0F1B2D;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid #E3E8EE">${esc(it.heading)}</td></tr>`;
        continue;
      }
      if (it.group) {
        body += `<tr><td colspan="2" style="${font}padding:10px 14px;background:#E7F2EF;font-size:14px;font-weight:bold;color:#08564A;border-bottom:1px solid #E3E8EE">${esc(it.group)}</td></tr>`;
      }
      body += it.rows.map(rowHtml).join("");
    }
    body += `</table></td></tr>`;
  }

  const summary = [
    ...(d.company ? [{ label: "Corporation", value: d.company }] : []),
    { label: d.company ? "Contact" : "Client", value: d.name },
    { label: "Email", value: d.email },
    { label: "Phone", value: d.phone || "-" },
    { label: "Submitted", value: d.submitted },
    { label: "Applies to", value: d.applies.length ? d.applies.join(", ") : "-" },
  ].map(rowHtml).join("");

  return `<!doctype html><html><body style="margin:0;padding:0;background:#F4F7F6">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F7F6"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#FFFFFF;border-radius:10px">
<tr><td style="background:#0B6E5F;padding:22px 28px;border-radius:10px 10px 0 0">
<div style="${font}color:#CFEDE6;font-size:12px;letter-spacing:.08em;text-transform:uppercase">Calcitax Advisors · New client form</div>
<div style="${font}color:#FFFFFF;font-size:24px;font-weight:bold;margin-top:6px">${esc(d.title)}</div>
<div style="${font}color:#CFEDE6;font-size:14px;margin-top:4px">${esc(d.subtitle)}</div>
</td></tr>
<tr><td style="padding:8px 28px 28px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:20px 0 8px"><div style="${font}font-size:18px;font-weight:bold;color:#0B6E5F">Summary</div></td></tr>
<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E3E8EE;border-radius:8px;border-collapse:separate;overflow:hidden">${summary}</table></td></tr>
${body}
<tr><td style="${font}padding:28px 0 0;font-size:13px;color:#4A5568">Reply to this email to contact ${esc(d.name)} directly. Ask the client to send documents${d.kind === "t2" ? "" : " and their SIN"} through a secure method, not by regular email.</td></tr>
</table>
</td></tr>
</table>
</td></tr></table>
</body></html>`;
}

function buildMultipartEmail({ replyTo, subject, text, html }) {
  const boundary = `calcitax-${crypto.randomUUID()}`;
  return [
    `From: Calcitax Website <${FROM_ADDRESS}>`,
    `To: ${TO_ADDRESS}`,
    `Reply-To: ${replyTo}`,
    `Subject: ${encodeHeader(subject)}`,
    `Date: ${new Date().toUTCString()}`,
    `Message-ID: <${crypto.randomUUID()}@calcitax.com>`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    "",
    `--${boundary}`,
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    wrap(base64(text)),
    `--${boundary}`,
    "Content-Type: text/html; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    wrap(base64(html)),
    `--${boundary}--`,
    "",
  ].join("\r\n");
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function clean(value) {
  return typeof value === "string" ? value.trim() : "";
}

// Strip line breaks so user input can't inject extra email headers.
function oneLine(value) {
  return clean(value).replace(/[\r\n]+/g, " ");
}

function isEmail(value) {
  return /^[^\s@<>()",;:]+@[^\s@<>()",;:]+\.[^\s@<>()",;:]{2,}$/.test(value);
}

function base64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

function wrap(text) {
  return text.match(/.{1,76}/g).join("\r\n");
}

function encodeHeader(text) {
  return `=?UTF-8?B?${base64(text)}?=`;
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
