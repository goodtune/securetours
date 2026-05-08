import express from 'express';
import { Resend } from 'resend';

const app = express();
app.use(express.json({ limit: '32kb' }));
app.use(express.urlencoded({ extended: false, limit: '32kb' }));

const PORT = parseInt(process.env.PORT ?? '3000', 10);
const RESEND_API_KEY = process.env.RESEND_API_KEY;
const TO = process.env.CONTACT_TO_ADDRESS ?? 'enquiries@securetours.com.au';
const FROM = process.env.CONTACT_FROM_ADDRESS ?? 'noreply@securetours.com.au';

if (!RESEND_API_KEY) {
  console.warn('[contact-api] RESEND_API_KEY not set — /api/contact will return 503');
}

const resend = RESEND_API_KEY ? new Resend(RESEND_API_KEY) : null;

const HTML_ESCAPE = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => HTML_ESCAPE[c]);

const isEmail = (s) =>
  typeof s === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s) && s.length <= 254;

app.get('/health', (_req, res) => res.json({ ok: true }));
app.get('/api/health', (_req, res) => res.json({ ok: true }));

app.post('/api/contact', async (req, res) => {
  const body = req.body ?? {};

  // Honeypot — silently accept and drop. Bots fill all fields; humans don't
  // see the hidden input. We return 200 so bots don't iterate looking for
  // the failure mode.
  if (body.website && String(body.website).trim() !== '') {
    return res.json({ ok: true });
  }

  const first_name = String(body.first_name ?? '').trim().slice(0, 120);
  const last_name = String(body.last_name ?? '').trim().slice(0, 120);
  const email = String(body.email ?? '').trim().slice(0, 254);
  const phone = String(body.phone ?? '').trim().slice(0, 60);
  const service = String(body.service ?? '').trim().slice(0, 60);
  const message = String(body.message ?? '').trim().slice(0, 5000);

  if (!first_name || !last_name || !email || !message) {
    return res.status(400).json({
      error: 'Please fill in your name, email, and message.',
    });
  }
  if (!isEmail(email)) {
    return res.status(400).json({ error: 'Please provide a valid email address.' });
  }

  if (!resend) {
    return res.status(503).json({
      error: 'Email service not configured. Please call us on +61 414 499 778.',
    });
  }

  const subject = `New enquiry — ${first_name} ${last_name}${service ? ` · ${service}` : ''}`;
  const lines = [
    `<h2 style="font-family:Georgia,serif;color:#1E2E78;">New enquiry from securetours.com.au</h2>`,
    `<table style="font-family:Arial,sans-serif;font-size:14px;border-collapse:collapse;">`,
    `  <tr><td style="padding:4px 12px 4px 0;color:#666;">Name</td><td>${escapeHtml(first_name)} ${escapeHtml(last_name)}</td></tr>`,
    `  <tr><td style="padding:4px 12px 4px 0;color:#666;">Email</td><td><a href="mailto:${escapeHtml(email)}">${escapeHtml(email)}</a></td></tr>`,
    phone ? `  <tr><td style="padding:4px 12px 4px 0;color:#666;">Phone</td><td>${escapeHtml(phone)}</td></tr>` : '',
    service ? `  <tr><td style="padding:4px 12px 4px 0;color:#666;">Solution</td><td>${escapeHtml(service)}</td></tr>` : '',
    `</table>`,
    `<hr style="border:none;border-top:1px solid #ddd;margin:16px 0;">`,
    `<div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;white-space:pre-wrap;">${escapeHtml(message)}</div>`,
  ].filter(Boolean).join('\n');

  try {
    const result = await resend.emails.send({
      to: TO,
      from: FROM,
      replyTo: email,
      subject,
      html: lines,
    });

    if (result.error) {
      console.error('[contact-api] resend error:', result.error);
      return res
        .status(502)
        .json({ error: 'We could not deliver your enquiry. Please call us on +61 414 499 778.' });
    }

    return res.json({ ok: true });
  } catch (err) {
    console.error('[contact-api] resend exception:', err);
    return res
      .status(502)
      .json({ error: 'We could not deliver your enquiry. Please call us on +61 414 499 778.' });
  }
});

app.use((req, res) => res.status(404).json({ error: 'Not found' }));

app.listen(PORT, () => {
  console.log(`[contact-api] listening on :${PORT}`);
});
