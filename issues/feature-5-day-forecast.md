# Feature: 5-day Forecast View

## Summary
Add a 5-day forecast page that shows daily high/low temperatures, conditions, and an icon for each day. Include an optional compact chart (sparkline) for temperature trend.

## Motivation
Users often want to see upcoming weather, not just the current conditions.

## Acceptance criteria
- A new route (`/forecast` or `/forecast?city=...`) returns a 5-day forecast for the selected city.
- Each day shows date, high/low temps, condition text, and an icon.
- A small temperature trend chart or sparkline is present (SVG or small canvas).
- Graceful error handling for cities with no forecast data.

## Implementation notes
- Use the existing geocoding lookup to get lat/lon, then call the weather API's multi-day forecast endpoint.
- Add a new template `templates/forecast.html` and a link from the main result card.
- Consider caching responses for a short time to reduce API calls.

## Suggested labels
enhancement, frontend, backend
