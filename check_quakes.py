import json
import math
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

NTFY_TOPIC = os.environ['NTFY_TOPIC']
LAT = float(os.environ.get('LAT') or '32.7157')
LON = float(os.environ.get('LON') or '-117.1611')
PLACE = os.environ.get('PLACE') or 'San Diego'
RADIUS_MILES = float(os.environ.get('RADIUS_MILES') or '100')
MIN_MAGNITUDE = float(os.environ.get('MIN_MAGNITUDE') or '4.0')
TIMEZONE = os.environ.get('TIMEZONE') or 'America/Los_Angeles'

SEEN_FILE = 'seen.json'


def load_state():
    try:
        with open(SEEN_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {'alerted_ids': []}


def save_state(state):
    with open(SEEN_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def fetch_quakes():
    url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
    start = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
    params = {
        'format': 'geojson',
        'latitude': LAT,
        'longitude': LON,
        'maxradiuskm': RADIUS_MILES * 1.60934,
        'minmagnitude': MIN_MAGNITUDE,
        'starttime': start,
        'orderby': 'time',
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get('features', [])


def miles_away(qlat, qlon):
    r = 3958.8
    p1, p2 = math.radians(LAT), math.radians(qlat)
    dp = math.radians(qlat - LAT)
    dl = math.radians(qlon - LON)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def notify(quake):
    props = quake['properties']
    qlon, qlat, depth_km = quake['geometry']['coordinates']
    mag = props.get('mag') or 0
    place = props.get('place') or 'location unknown'
    when = datetime.fromtimestamp(props['time'] / 1000, tz=ZoneInfo(TIMEZONE))
    message = (
        f"{when.strftime('%a %-I:%M %p %Z')} - "
        f"{miles_away(qlat, qlon):.0f} mi from {PLACE}, {depth_km:.0f} km deep"
    )
    requests.post(
        f'https://ntfy.sh/{NTFY_TOPIC}',
        data=message.encode(),
        headers={
            'Title': f'M{mag:.1f} earthquake: {place}'.encode(),
            'Priority': 'urgent' if mag >= 5.5 else 'high',
            'Click': props.get('url') or 'https://earthquake.usgs.gov/earthquakes/map/',
        },
    )


def main():
    state = load_state()
    alerted = state.get('alerted_ids', [])
    quakes = fetch_quakes()
    new = [q for q in quakes if q['id'] not in alerted]

    print(f"{len(quakes)} quakes M{MIN_MAGNITUDE}+ within {RADIUS_MILES:.0f} mi in last 24h, {len(new)} new")

    for quake in sorted(new, key=lambda q: q['properties']['time']):
        notify(quake)
        alerted.append(quake['id'])
        props = quake['properties']
        print(f"Alerted: {quake['id']} M{props.get('mag')} {props.get('place')}")

    if new:
        state['alerted_ids'] = alerted[-500:]
        save_state(state)


if __name__ == '__main__':
    main()
