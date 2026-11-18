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


def render_dates(site, page, dates, section, track, track_index):
    items = []
    kind = 'sitting' if section == 'sittings' else 'hearing'
    ordered = sorted(dates, key=lambda item: (item['start'], item.get('time', '')))
    for event_index, entry in enumerate(ordered):
        start = entry['start']
        end = entry.get('end', start)
        event_id = f'calendar-event-{kind}-{track_index}-{event_index}'
        attributes = f'id="{event_id}" data-cal-event data-start="{start}" data-end="{end}" data-kind="{kind}" data-track="{site.e(track)}"'
        if entry.get('provisional'):
            attributes += ' data-provisional'
        details = ''
        if entry.get('time'):
            details += '<span class="calendar-event-time">' + site.e(entry['time']) + '</span>'
        if entry.get('title'):
            title = entry['title']
            details += '<span class="calendar-event-title">' + (site.link(page, entry['url'], title) if entry.get('url') else site.e(title)) + '</span>'
        if entry.get('note'):
            details += '<small class="calendar-event-note">' + site.e(entry['note']) + '</small>'
        if details:
            details = '<div class="calendar-event-detail">' + details + '</div>'
        items.append(f'<li {attributes}><strong class="calendar-event-date">{date_markup(start, end)}</strong>{details}</li>')
    return '<ol class="calendar-dates">' + ''.join(items) + '</ol>'


def render_track(site, page, track, timezone, section, track_index):
    body = '<article class="feature-panel calendar-track"><h3>' + site.e(track['name']) + '</h3>'
    dates = track.get('dates', [])
    if dates:
        body += '<p class="calendar-status" data-calendar-status="' + site.e(timezone) + '" hidden></p>'
        body += render_dates(site, page, dates, section, track['name'], track_index)
    if track.get('note'):
        body += '<p>' + site.e(track['note']) + '</p>'
    body += '<ul class="calendar-links">'
    for source in track['links']:
        body += '<li>' + site.link(page, source['url'], source['label']) + '</li>'
    return body + '</ul></article>'


def month_board(site, timezone):
    weekdays = ''.join(f'<span>{day}</span>' for day in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'))
    legend = ''.join(f'<li><span class="calendar-mark is-{kind}" aria-hidden="true"></span>{label}</li>' for kind, label in (
        ('sitting', 'Chamber sitting'), ('hearing', 'Committee hearing'), ('provisional', 'Check status')
    ))
    return f'''
<section class="calendar-board feature-panel" data-parliament-calendar="{site.e(timezone)}" aria-labelledby="month-view" hidden>
  <div class="calendar-board-header">
    <h2 id="month-view">Month view</h2>
    <div class="calendar-controls">
      <button type="button" data-cal-prev aria-label="Previous month"><span aria-hidden="true">‹</span></button>
      <select data-cal-month aria-label="Calendar month"></select>
      <button type="button" data-cal-next aria-label="Next month"><span aria-hidden="true">›</span></button>
    </div>
  </div>
  <div class="calendar-board-content">
    <div class="calendar-month">
      <div class="calendar-weekdays" aria-hidden="true">{weekdays}</div>
      <ol class="calendar-days" data-cal-days aria-label="Dates in the selected month"></ol>
      <ul class="calendar-legend" aria-label="Calendar legend">{legend}</ul>
    </div>
    <div class="calendar-day-detail" aria-live="polite" aria-atomic="true">
      <h3 data-cal-date></h3>
      <ul class="calendar-day-events" data-cal-events></ul>
      <p data-cal-empty hidden></p>
    </div>
  </div>
</section>'''


def build_calendars(site):
    calendars = load_calendars()
    page = 'calendars/index.html'
    body = site.hero('Parliament calendars.', 'Choose a parliament to see sitting dates, public committee hearings and links to official calendars.', cls='directory-hero')
    for keys, heading, cls in [
        (ORDER[:2], 'Queensland and Australian Parliament', 'calendar-picker-featured'),
        (ORDER[2:], 'Other states and territories', 'calendar-picker-regions'),
    ]:
        body += f'<section class="calendar-picker"><h2>{heading}</h2><div class="parliament-grid {cls}">'
        for key in keys:
            calendar = calendars[key]
            url = site.e(site.rel(page, site.browse_route('calendars', key)))
            body += f'<a class="parliament-choice" href="{url}"><h3>{site.e(calendar["name"])}</h3><p>{site.e(calendar["summary"])}</p><span aria-hidden="true">›</span></a>'
        body += '</div></section>'
    site.write(page, 'Parliament calendars', body)

    for key in ORDER:
        calendar = calendars[key]
        name = calendar['name']
        page = f'calendars/{key}/index.html'
        body = site.hero(f'{name} calendar.', calendar['summary'], 'P4A · Parliament calendars', cls='directory-hero calendar-hero')
        if any(track.get('dates') for section in ('sittings', 'hearings') for track in calendar[section]):
            body += month_board(site, calendar['timezone'])
        else:
            body += '<p class="notice">No future dates have been verified. Official calendar and hearing links are below.</p>'
        checked = site.pretty_date(calendar['checked'])
        body += f'<p class="status-strip"><span>Sources checked <time datetime="{calendar["checked"]}">{checked}</time>.</span><span>See official programs for updates.</span></p>'
        body += '<nav class="council-sections" aria-label="On this calendar">'
        body += site.link(page, '#sittings', 'Chamber sittings') + site.link(page, '#hearings', 'Committee hearings')
        body += site.link(page, 'calendars/', 'Choose another parliament') + '</nav>'
        for section, heading, kind in [('sittings', 'Chamber sittings', 'sitting'), ('hearings', 'Committee hearings', 'hearing')]:
            body += f'<section class="calendar-section" id="{section}"><h2><span class="calendar-mark is-{kind}" aria-hidden="true"></span>{heading}</h2>'
            if section == 'hearings':
                body += '<p>Check each hearing’s program for attendance and streaming details. Invitations to give evidence and submission deadlines are published separately.</p>'
            body += '<div class="calendar-tracks">'
            for track_index, track in enumerate(calendar[section]):
                body += render_track(site, page, track, track.get('timezone', calendar['timezone']), section, track_index)
            body += '</div></section>'
        site.write(page, f'{name} calendar', body)
