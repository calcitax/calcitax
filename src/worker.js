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
