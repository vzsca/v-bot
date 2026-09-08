# v-bot Web Panel — In Process

This directory contains the frontend-only preview of the future v-bot web control panel.

## Current state

The panel is **in process**. It currently provides the UI and interaction layer, but it is not connected to the real bot or a backend yet.

- HTML/CSS/JS only.
- Login screen with panel ID and password fields.
- The Connect button currently enters the panel without validating credentials.
- No account creation or authentication backend exists yet.
- Sidebar navigation with hash-based pages.
- Browser Back/Forward navigation support.
- Direct page URLs are preserved through the login screen.
- Server management popups and confirmation dialogs.
- Frontend-only actions for bot control, logs, owners and configuration.
- Keyboard and screen-reader accessibility improvements.
- No real credential validation, API calls, process control, file writes, or bot actions.
- The existing bot and CLI panel are intentionally untouched.

## Authentication preview

The login screen is currently **UI-only**. The ID and password fields are present so the final authentication flow can be implemented later.

The current Connect action only opens the panel and does not store credentials or create a session.

The future backend must perform the real ID/password validation, session management and server-side authorization.

## Local preview

Because the panel uses JavaScript modules, it should be served through a small local HTTP server rather than opened directly with `file://`.

From the repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/panel_web/
```

## Structure

```text
panel_web/
├── README.md
├── index.html
└── assets/
    ├── app.js
    ├── auth.js
    ├── auth.css
    ├── accessibility.js
    ├── actions.js
    ├── modals.js
    ├── navigation.js
    ├── servers.js
    ├── style.css
    ├── ui.css
    └── polish.css
```
