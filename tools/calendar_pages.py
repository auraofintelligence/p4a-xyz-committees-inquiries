"""Generate one calendar index and one schedule page per parliament."""

import json
from datetime import date
from pathlib import Path


CALENDAR_DATA = Path(__file__).resolve().parents[1] / 'data' / 'parliament-calendars.json'
ORDER = ('qld', 'federal', 'nsw', 'vic', 'wa', 'sa', 'tas', 'act', 'nt')


def load_calendars():
    return json.loads(CALENDAR_DATA.read_text(encoding='utf-8'))


def calendar_map():
    calendars = load_calendars()
    return [('calendars/index.html', 'Choose a parliament calendar')] + [
        (f'calendars/{key}/index.html', f"{calendars[key]['name']} calendar") for key in ORDER
    ]


def date_markup(start, end):
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    if first == last:
        return f'<time datetime="{start}">{first.strftime("%a")} {first.day} {first.strftime("%B %Y")}</time>'
    if (first.year, first.month) == (last.year, last.month):
        first_label = str(first.day)
    elif first.year == last.year:
        first_label = f'{first.day} {first.strftime("%B")}'
    else:
        first_label = f'{first.day} {first.strftime("%B %Y")}'
    return f'<time datetime="{start}">{first_label}</time> to <time datetime="{end}">{last.day} {last.strftime("%B %Y")}</time>'


def render_dates(site, page, dates):
    items = []
    for entry in sorted(dates, key=lambda item: (item['start'], item.get('time', ''))):
        start = entry['start']
        end = entry.get('end', start)
        content = '<strong>' + date_markup(start, end) + '</strong>'
        if entry.get('time'):
            content += ' · ' + site.e(entry['time'])
        if entry.get('title'):
            title = entry['title']
            content += '<span>' + (site.link(page, entry['url'], title) if entry.get('url') else site.e(title)) + '</span>'
        if entry.get('note'):
            content += '<small>' + site.e(entry['note']) + '</small>'
        day_range = '' if entry.get('provisional') else f' data-calendar-start="{start}" data-calendar-end="{end}"'
        items.append('<li' + day_range + '>' + content + '</li>')
    return '<ol class="calendar-dates">' + ''.join(items) + '</ol>'


def render_track(site, page, track, timezone):
    body = '<article class="feature-panel calendar-track"><h3>' + site.e(track['name']) + '</h3>'
    dates = track.get('dates', [])
    if dates:
        body += '<p class="calendar-status" data-calendar-status="' + site.e(timezone) + '" hidden></p>'
        body += render_dates(site, page, dates)
    if track.get('note'):
        body += '<p>' + site.e(track['note']) + '</p>'
    body += '<ul class="calendar-links">'
    for source in track['links']:
        body += '<li>' + site.link(page, source['url'], source['label']) + '</li>'
    return body + '</ul></article>'


def build_calendars(site):
    calendars = load_calendars()
    page = 'calendars/index.html'
    body = site.hero('Parliament calendars.', 'Choose a parliament to see sitting dates, public committee hearings and links to official calendars.', cls='directory-hero')
    body += '<div class="parliament-grid">'
    for key in ORDER:
        calendar = calendars[key]
        url = site.e(site.rel(page, site.browse_route('calendars', key)))
        body += f'<a class="parliament-choice" href="{url}"><h2>{site.e(calendar["name"])}</h2><p>{site.e(calendar["summary"])}</p><span aria-hidden="true">›</span></a>'
    site.write(page, 'Parliament calendars', body + '</div>')

    for key in ORDER:
        calendar = calendars[key]
        name = calendar['name']
        page = f'calendars/{key}/index.html'
        body = site.hero(f'{name} calendar.', calendar['summary'], 'P4A · Parliament calendars', cls='directory-hero')
        checked = site.pretty_date(calendar['checked'])
        body += f'<p class="status-strip">Sources checked <time datetime="{calendar["checked"]}">{checked}</time>. Use the official programs for updates and the full schedules.</p>'
        body += '<nav class="council-sections" aria-label="On this calendar">'
        body += site.link(page, '#sittings', 'Chamber sittings') + site.link(page, '#hearings', 'Committee hearings')
        body += site.link(page, 'calendars/', 'Choose another parliament') + '</nav>'
        for section, heading in [('sittings', 'Chamber sittings'), ('hearings', 'Committee hearings')]:
            body += f'<section class="calendar-section" id="{section}"><h2>{heading}</h2>'
            if section == 'hearings':
                body += '<p>Check each hearing’s program for attendance and streaming details. Invitations to give evidence and submission deadlines are published separately.</p>'
            body += '<div class="calendar-tracks">'
            for track in calendar[section]:
                body += render_track(site, page, track, track.get('timezone', calendar['timezone']))
            body += '</div></section>'
        site.write(page, f'{name} calendar', body)
