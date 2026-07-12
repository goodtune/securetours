# CMS Auth Setup (Sveltia CMS + GitHub OAuth)

This document is the runbook for wiring up GitHub-based sign-in for the Sveltia CMS admin panel at `/admin`, using [`sveltia-cms-auth`](https://github.com/sveltia/sveltia-cms-auth) as the OAuth proxy, deployed to Cloudflare Workers.

The order below matters: the Worker has to exist first because its URL becomes the OAuth callback.

## 1. Deploy the Worker (get its URL first)

You need a Cloudflare account — the free plan is fine (the auth flow is a handful of requests per editor session, nowhere near the free 100k requests/day).

**Easy path (no CLI):** open https://github.com/sveltia/sveltia-cms-auth and click the "Deploy to Cloudflare Workers" button in the README. It forks the repo into your GitHub account and creates the Worker via Cloudflare's connect flow.

**CLI path (if you prefer):**

```sh
git clone https://github.com/sveltia/sveltia-cms-auth
cd sveltia-cms-auth
npx wrangler login
npx wrangler deploy
```

Either way, note the Worker URL from the Cloudflare dashboard — it looks like:

`https://sveltia-cms-auth.<your-subdomain>.workers.dev`

Don't configure anything else yet; it won't work until step 3.

## 2. Register the GitHub OAuth App

Do this on the account that owns the repo (`goodtune`): GitHub → **Settings → Developer settings → OAuth Apps → New OAuth App** (direct link: https://github.com/settings/applications/new), then:

- **Application name:** `Secure Tours CMS` (the client admin sees this on the consent screen)
- **Homepage URL:** `https://securetours.com.au`
- **Authorization callback URL:** `<YOUR_WORKER_URL>/callback` — e.g. `https://sveltia-cms-auth.<your-subdomain>.workers.dev/callback` (the `/callback` path is required)

Register it, then **note the Client ID** and click **Generate a new client secret** — copy the secret immediately, it's shown once.

Note: the OAuth app itself grants nothing — a signed-in user can only do what their GitHub account can do on the repo. Access control stays with repo collaborator permissions.

## 3. Configure the Worker

Cloudflare dashboard → your Worker → **Settings → Variables and Secrets**, add:

| Name | Value | Type |
|---|---|---|
| `GITHUB_CLIENT_ID` | from step 2 | plaintext is fine |
| `GITHUB_CLIENT_SECRET` | from step 2 | **Secret** (encrypted) |
| `ALLOWED_DOMAINS` | `securetours.com.au, www.securetours.com.au, securetours-staging-6i7a4.ondigitalocean.app` | plaintext |

`ALLOWED_DOMAINS` is what stops other sites from using your auth helper — keep it current if the staging URL ever changes (wildcards like `*.ondigitalocean.app` are supported but that's too broad; use the exact hostname). Save and redeploy the Worker if prompted.

## 4. Set `CMS_AUTH_BASE_URL` on both DO apps

This is a **build-time** variable — Astro bakes it into `/admin/config.yml` when the site builds, so it must be scoped to the build, and a rebuild is needed for it to take effect.

For **each** app (production and staging): DO dashboard → app → **Settings → the static-site component → Environment Variables → Edit**, add:

```
CMS_AUTH_BASE_URL = https://sveltia-cms-auth.<your-subdomain>.workers.dev
```

(the Worker URL with no trailing path). Scope: Build Time (or "Build and Run" — run scope is simply unused). Saving triggers a redeploy; if not, hit **Actions → Force Rebuild and Deploy**.

## 5. Verify

1. `curl https://securetours-staging-6i7a4.ondigitalocean.app/admin/config.yml` — the `backend` block should now include `"base_url": "https://sveltia-cms-auth...workers.dev"`. (`config.yml.ts` is wired to include it only when the env var is set, so its presence confirms the var reached the build.)
2. Open `/admin` on staging — the login screen now shows **"Sign in with GitHub"** instead of the token prompt. Sign in; first time through, GitHub shows the consent screen for "Secure Tours CMS" → Authorize.
3. Make a trivial edit, save, and confirm the commit lands on `feature/admin-cms` and staging redeploys.
4. Repeat check 1–2 on `https://securetours.com.au/admin/` after PR #6 merges (production's `/admin` doesn't exist until then — no need to set the var on production before merging, just don't forget it).

**Common failure modes:** a redirect loop or "callback URL mismatch" error means the OAuth app's callback URL doesn't exactly match `<worker>/callback`; an "unauthorized domain" style error means the requesting site's hostname isn't in `ALLOWED_DOMAINS`; a sign-in that works but can't save means the signed-in GitHub user lacks write access to `goodtune/securetours` — add them as a collaborator.
