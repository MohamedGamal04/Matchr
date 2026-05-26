// Runtime config — loaded BEFORE every other script in index.html.
//
// Edit these two values when deploying:
//   • MATCHR_API     → the backend URL (e.g. https://user-matchr-backend.hf.space)
//   • MATCHR_API_KEY → the X-API-Key gating /api/ingest/* and /api/scrape/*
//                      Leave null when running an open-access local build.
//
// Treat MATCHR_API_KEY as "public-ish": it sits in the browser, so anyone
// with DevTools can read it. It's a friction barrier against casual abuse,
// not real auth.

window.MATCHR_API     = 'http://localhost:8000';
window.MATCHR_API_KEY = null;
