# Feature: City Autocomplete & Recent Searches

## Summary
Add an autocomplete dropdown for the city input that suggests matching places as the user types and store recent searches for quick selection.

## Motivation
Reduces typing errors and helps users find the correct city quickly (e.g., multiple cities with same name).

## Acceptance criteria
- Typing in the city input shows live suggestions (debounced) from the geocoding API.
- Selecting a suggestion fills the input and, optionally, triggers the lookup.
- Recent searches are stored in a small local cache (browser localStorage) and shown under the input.
- UI remains responsive on mobile.

## Implementation notes
- Use a small JS script to call an internal route like `/suggest?q=...` that proxies to the geocoding API.
- Debounce user input (~300ms) and limit suggestions to 5 items.
- Keep recent searches in `localStorage` with a max length (e.g., 6 entries).

## Suggested labels
feature, frontend, ux
