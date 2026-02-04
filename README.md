# Earnings Call.biz Webhook Receiver

A small Python webhook endpoint you can deploy to **Vercel** (or similar) to receive and inspect payloads from [earnings call.biz](https://earningscall.biz) or any other service.

## What it does

- **POST** to `/api/webhook`: Accepts the webhook, captures **everything** (method, path, query, headers, raw body, and parsed JSON if applicable), optionally saves it to Vercel Blob, and **returns the full captured payload** in the response so you can see the exact format.
- **GET** `/api/webhook`: Returns a short usage message.
- **GET** `/api/webhooks/list`: Lists recently saved webhook payloads (only when Blob is configured).

## Deploy to Vercel

1. **Install Vercel CLI** (if needed):
   ```bash
   npm i -g vercel
   ```

2. **Deploy** from this directory:
   ```bash
   cd /path/to/webhook
   vercel
   ```
   Follow the prompts (link to existing project or create new one). You’ll get a URL like `https://your-project.vercel.app`.

3. **Webhook URL for earnings call.biz**  
   Use:
   ```text
   https://your-project.vercel.app/api/webhook
   ```
   Configure this in the earnings call.biz dashboard as the webhook / callback URL.

## Seeing what they send

- **In the response**: Send a POST (or let earnings call.biz send one). The response body is JSON with a `captured` object containing:
  - `received_at`
  - `method`, `path`, `query`
  - `headers`
  - `body_raw` (raw string)
  - `body_parsed` (parsed JSON if the body was valid JSON)

- **In Vercel**: In the Vercel dashboard, open your project → **Logs** or **Functions** and click the invocation for `/api/webhook` to see logs and the payload.

- **Optional – save every webhook**: Add [Vercel Blob](https://vercel.com/docs/storage/vercel-blob) to the project and set the env var `BLOB_READ_WRITE_TOKEN` for the project. Then each POST will be stored under `webhooks/earnings/` and you can list them with:
  ```text
  GET https://your-project.vercel.app/api/webhooks/list?limit=20
  ```
  Each listed blob has a `url` you can open to download that JSON file.

## Deploy elsewhere (e.g. Railway, Render, Fly.io)

The app is a single Python HTTP handler. To run it on another platform:

1. Use a small WSGI server (e.g. **Gunicorn** or **Waitress**) and wrap the handler, or
2. Expose the same logic as a **FastAPI/Flask** route that:
   - Reads request headers and body.
   - Builds the same `captured` structure.
   - Optionally saves to a file or database.
   - Returns `{"ok": true, "captured": ...}`.

The important part is to capture and return the full request (headers + body) so you can see exactly what earnings call.biz sends.

## Local test

```bash
# From project root
pip install -r requirements.txt

# Use Vercel dev to run the serverless functions locally
npx vercel dev
```

Then:

```bash
curl -X POST https://localhost:3000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "hello"}'
```

You should see the full captured payload in the response.
