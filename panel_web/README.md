# v-bot Web Panel — In Process

The `panel_web` directory contains the frontend preview of the future v-bot web control panel.

## Current state

The web panel is **frontend-only**. It is currently used to validate the interface, navigation and user experience before connecting a real backend.

The panel has been tested through GitHub Pages and the current frontend flows are working as expected.

Current capabilities:

- Modern responsive administration UI.
- Login/connection screen with Panel ID and Password fields.
- Frontend-only connection state stored in the browser session.
- Protected hash-based navigation.
- Direct links to panel pages.
- Browser Back/Forward navigation.
- Responsive mobile sidebar.
- Dashboard, status, bot control, servers, logs, security, owners, Discord, integrations, security settings, updates and about pages.
- Server management, invite, API access and leave dialogs.
- Preview dialogs for process, configuration and management actions.
- Keyboard focus handling and accessible navigation states.
- Modal focus trapping and Escape-to-close behavior.
- Reduced-motion support.

## Authentication preview

Authentication is currently a **UI simulation**.

The form accepts the Panel ID and Password fields but does not validate them against a backend. Clicking **Connect** creates a frontend session in `sessionStorage` and opens the Dashboard.

The current session behavior is:

```text
Not connected + #dashboard
        ↓
    #connexion

Connect
        ↓
    #dashboard

Connected + any valid page
        ↓
    Requested page

Connected + #connexion
        ↓
    #dashboard
```

No credentials are sent to a server and no real authentication security exists yet.

The future backend must handle authentication, authorization, sessions, expiration, CSRF protection and secure credential storage.

## Navigation

Navigation uses URL hashes so the frontend can switch views without a page reload.

Available routes:

```text
#connexion
#dashboard
#status
#control
#servers
#logs
#security
#owners
#discord
#integrations
#security-settings
#updates
#about
```

The current controller keeps the requested valid route when navigating and falls back to `#dashboard` only for unknown routes.

The sidebar links are marked with `aria-current="page"` when active.

## Interaction model

The current web panel deliberately separates **navigation** from **preview actions**.

Navigation actions such as opening Dashboard, Status or Servers change the current frontend view.

Management actions such as Start, Stop, Restart, Save Changes, Add Owner, Search Servers or Leave Server currently open frontend dialogs and display preview feedback. They do not modify the bot, the filesystem, Discord or external APIs.

This makes the frontend safe to use while the backend is still under development.

## UI sections

### Dashboard

Provides the main overview with:

- Bot status.
- Current version.
- Connected server count.
- Memory usage preview.
- Quick process actions.
- Latest release information.

### Status

Shows a preview of process and configuration information such as PID, uptime, CPU, RAM, Python version and platform.

### Bot Control

Contains Start, Stop and Restart controls. They are currently visual placeholders.

### Servers

Displays connected Discord server cards with:

- Server status.
- Member count.
- Channel count.
- Bot access level.
- Manage.
- Invite.
- API Access.
- Leave.

All server data is static preview data at this stage.

### Bot Logs

Provides a readable log viewer mockup.

### Security Logs

Provides an audit/security event preview without exposing secrets.

### Owners

Provides the future owner-management interface, including the principal owner and secondary owners.

### Discord

Provides a preview of bot-wide Discord configuration such as prefix and token status.

### Integrations

Provides Twitch and YouTube configuration previews.

### Security

Provides previews for sensitive-command state, one-time action codes, audit logging and the kill switch.

### Updates

Provides release/update information and a future update-check entry point.

### About

Provides a short description of v-bot and the current panel version.

## Accessibility

The panel includes frontend accessibility improvements:

- Skip-to-content link.
- Focus-visible states.
- Keyboard-accessible controls.
- `aria-current` for the active navigation page.
- Accessible mobile navigation state.
- Focus management for modals.
- Modal focus trapping.
- Escape-to-close behavior.
- Accessible dialog labels where applicable.
- Reduced-motion support.

## Architecture

The current repository still contains several modular frontend files from earlier iterations, but `assets/app.js` is currently the active frontend controller and owns the effective routing/auth/modal behavior.

```text
panel_web/
├── README.md
├── index.html
└── assets/
    ├── app.js
    ├── navigation.js
    ├── auth.js
    ├── actions.js
    ├── modals.js
    ├── servers.js
    ├── accessibility.js
    ├── style.css
    ├── ui.css
    ├── auth.css
    └── polish.css
```

The existing modular files are retained for the moment so the frontend can continue evolving without changing the working GitHub Pages version unnecessarily.

## Audit summary

### Navigation

**Status: PASS**

The active controller correctly handles:

- unauthenticated access to protected routes;
- connection state;
- valid hash routes;
- unknown routes;
- direct route loading;
- navigation between pages;
- browser history navigation;
- mobile sidebar state.

### Usage

**Status: PASS for frontend preview**

The panel can currently be used as a realistic administration UI mockup. Buttons provide visual feedback or open dialogs rather than executing real operations.

### Authentication

**Status: PASS for preview / NOT READY for production**

The current browser-session connection flow behaves as designed, but it is not a security boundary. Credentials are not validated and the session is not backed by a server.

### Backend integration

**Status: NOT IMPLEMENTED**

There are currently no real calls to:

- the Discord bot;
- local processes;
- configuration files;
- Discord APIs;
- Twitch APIs;
- YouTube APIs;
- GitHub release/update services.

## Local preview

From the repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/panel_web/
```

The project is also suitable for static hosting such as GitHub Pages.

## GitHub Pages

The frontend is designed to work as a static site. The panel can be opened from the repository's GitHub Pages deployment.

For cache-busting during frontend development, a query parameter can be appended to the page URL, for example:

```text
panel_web/?v=4#dashboard
```

## Development roadmap

```text
Frontend UI
    ↓
Navigation and UX validation
    ↓
Backend API
    ↓
Real authentication
    ↓
Bot/process control
    ↓
Discord/API integration
    ↓
Production hardening
```

The web panel should remain frontend-only until the interface and navigation are stable.

## Important security note

Never treat the current frontend connection screen as real authentication. Do not place Discord tokens, API keys or other secrets in the frontend source code.
