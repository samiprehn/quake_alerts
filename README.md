# Quake Alerts

Polls the [USGS earthquake API](https://earthquake.usgs.gov/fdsnws/event/1/) every 5 minutes and sends an [ntfy](https://ntfy.sh/) push notification when a M4.0+ earthquake hits within 100 miles of San Diego.

Answers "was that an earthquake?" before you've finished asking. Alerts once per quake — tap the notification for the full USGS event page.

## Fork this for your own area

1. **Fork this repo** (top right).
2. **Pick an ntfy topic** — any unique string, e.g. `quake-alerts-yourname-randomchars`. No registration needed; just pick something nobody else would guess.
3. **Install ntfy on your phone** — [iOS](https://apps.apple.com/us/app/ntfy/id1625396347) or [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) — subscribe to your topic.
4. **Add repository secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `NTFY_TOPIC` — from step 2
   - `LAT` / `LON` *(optional)* — your coordinates. Default: San Diego (32.7157, -117.1611)
   - `PLACE` *(optional)* — place name used in the notification. Default `San Diego`
   - `RADIUS_MILES` *(optional)* — alert radius. Default `100`
   - `MIN_MAGNITUDE` *(optional)* — minimum magnitude. Default `4.0`
   - `TIMEZONE` *(optional)* — IANA timezone for the quake time. Default `America/Los_Angeles`
5. **Allow the workflow to commit back** — Settings → Actions → General → Workflow permissions → Read and write permissions.
6. **Trigger a test run** — Actions tab → Check Quakes → Run workflow.

## How it works

Each run queries USGS for quakes above the magnitude floor within the radius over the last 24 hours (so nothing is missed if a few runs are skipped). New event IDs get one push each — magnitude ≥ 5.5 at ntfy `urgent` priority, otherwise `high` — then land in `seen.json` so revisions and later runs stay quiet. USGS sometimes revises magnitudes after the fact; the alert reflects whatever the feed said at send time.

Note: GitHub schedules 5-minute crons best-effort, so the real gap is usually 5–15 minutes. Fast enough to beat the local news, not a substitute for [ShakeAlert](https://www.shakealert.org/).

## Files

- `check_quakes.py` — main script
- `seen.json` — quake IDs already alerted (auto-updated by the workflow)
- `.github/workflows/check.yml` — GitHub Actions workflow, every 5 minutes

## Running locally

```
export NTFY_TOPIC=...
python check_quakes.py
```

To force test alerts from recent small quakes anywhere in SoCal, run with `MIN_MAGNITUDE=2.0 RADIUS_MILES=300` (then reset `seen.json`).
