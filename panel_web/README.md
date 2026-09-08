# v-bot Web Panel — In Process

This directory contains the frontend-only preview of the future v-bot web control panel.

## Current state

The panel is **in process**. It currently provides the complete UI/interaction layer, but it is not connected to the real bot or a backend yet.

- HTML/CSS/JS only.
- Login screen with panel ID and password fields.
- Frontend-only session login/logout flow.
- Change-password interface prepared for backend integration.
- Sidebar navigation with hash-based pages.
- Browser Back/Forward navigation support.
- Server management popups and confirmation dialogs.
- Frontend-only actions for bot control, logs, owners and configuration.
- Keyboard and screen-reader accessibility improvements.
- No real credential validation, API calls, process control, file writes, or bot actions.
- The existing bot and CLI panel are intentionally untouched.

## Authentication preview

The login screen is only a **mock authentication layer** at the moment. Any non-empty panel ID and password can pass the frontend check so the UI can be tested.

The session state is kept in `sessionStorage` and is cleared when the user logs out or the browser session ends.

The future backend must perform the real ID/password validation and server-side authorization.

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

Open `index.html` directly in a browser to preview the interface.
