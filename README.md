# Creatora

**Build your name. Share your vision.**

Creatora is an all-in-one business and portfolio platform built for visual creators — photographers, videographers, digital artists, illustrators, architects, influencers, beauty/lifestyle creators, and food creators. It's where work gets showcased, clients get managed, content gets planned, and shooting locations get discovered — all in one place.

## Try it

This project is deployed on a free hosting tier, which means the live instance spins down after periods of inactivity and can take up to a minute to wake back up on the first request, not ideal for a smooth first impression.

The best way to try Creatora is to run it locally.It takes about 2 minutes (see [Getting started](#getting-started) below) and comes with a pre-seeded database, so you'll see a fully populated app immediately, with no setup data to enter yourself.

## The problem it solves

Visual creators today juggle too many disconnected tools:

- A separate portfolio site to showcase work
- A spreadsheet to track clients and leads
- A notes app to remember shooting locations
- Instagram to post content with no real planning
- Email threads to manage bookings and inquiries

Creatora replaces that patchwork with one cohesive platform that speaks the language of creators — a public profile to get discovered, and a private dashboard to run the business behind it.

## Who it's for

| Role | Core need on the platform |
|---|---|
| Photographer | Portfolio, location scouting (SceneScout), client bookings |
| Videographer | Portfolio, SceneScout, content planning, collab board |
| Digital artist / illustrator / architect | Showcase work, client CRM, services & pricing |
| Influencer / content creator | Content calendar, brand collabs, analytics |
| Beauty & lifestyle creator | Look book, service bookings, testimonials |
| Food creator | Recipe/portfolio gallery, location collabs, brand deals |

Every creator gets the same toolset today — portfolio, services, shelf, CRM, planner, SceneScout, collabs, analytics, notifications — and picks which parts matter most to their workflow.

## Core modules

### Portfolio & Public Profile
Every creator gets a fully public profile (`/c/<username>`), no login required for visitors: a gallery of portfolio work with categories and featured pieces, a services & pricing list, approved client testimonials with star ratings, and a Digital Shelf for downloadable products (presets, templates, LUTs, guides, fonts, brushes, overlays). Visitors can send an inquiry directly from the profile.

### SceneScout
A community-powered location discovery map. Creators add shooting locations with category, vibe, best time to shoot, and crowd level, and they show up pinned on an interactive map (`/scenescout`) that anyone can browse and filter by category. It turns local creator knowledge into a shared resource — golden-hour rooftops, moody cafés, hidden trails, and more.

### Content Planner
A calendar/list view for planning posts across platforms (Instagram, TikTok, YouTube, etc.), with draft / scheduled / published statuses and notes per post — so creators always know what's coming next.

### Client CRM
Every inquiry submitted from a creator's public profile lands automatically in their CRM — no manual entry, no lost emails. Leads move through a pipeline: New → In Discussion → Booked → Completed.

### Collaboration Board
A public board (`/collabs`) where creators post open calls — "Looking for a videographer for a brand campaign in June" — and others can respond directly with their interest, no account required.

### Analytics
A dashboard view of profile views, inquiry volume and conversion rate, content stats by platform, collab activity, and total SceneScout contributions.

### Notification Center
In-app alerts for new inquiries, new testimonials, and collaboration interest, so creators stay on top of their business without checking every page.

## Why it stands out

- **SceneScout** — a genuinely unique feature most portfolio platforms don't offer
- **Zero friction for clients** — inquiries and testimonials without an account, discovery without barriers
- **Community-first** — the Collaboration Board and SceneScout turn individual profiles into a network
- **Full-stack depth** — file uploads, an interactive map, a content calendar, analytics, CRM, and public/private pages, all in one cohesive system

## Roadmap / not yet implemented

The current version is a strong working core. A few ideas from the original product vision are still on the roadmap:

- Role-specific dashboard layouts (today every creator sees the same dashboard, regardless of role)
- Structured "case study" portfolio entries (brief / challenge / solution / result)
- Curated SceneScout collections (e.g. "Wedding Locations", "Golden Hour Picks")
- "Someone viewed your profile" notifications
- Engagement-over-time charts in analytics
- Real payment processing for the Digital Shelf (currently simulated)

## Why "Creatora"?

The name combines "creator" — the core audience of the platform — with a refined, brand-style ending that gives it the feel of a modern digital product rather than a generic website. It reflects the broader vision: creating opportunities, connections, content, businesses, and careers — not just portfolios.

## Tech stack

- **Backend:** Python, Flask, Flask-SQLAlchemy (SQLite), Flask-Login
- **Frontend:** Jinja2 templates, Bootstrap 5, Bootstrap Icons, vanilla JavaScript
- **Maps:** Leaflet, with location data served as GeoJSON from a small JSON API

## Project structure

```
creatora/
├── app.py              # App factory, blueprints, error handlers, shelf download route
├── config.py           # Config (DB URI, upload settings, pagination)
├── models.py           # SQLAlchemy models
├── seed.py             # Populates the DB with demo creators/content (safe to re-run)
├── routes/
│   ├── auth.py         # Register, login, logout, password reset
│   ├── dashboard.py     # Private creator dashboard (portfolio, CRM, planner, shelf, etc.)
│   ├── public.py        # Public profile, directory, SceneScout, collabs
│   └── api.py           # JSON endpoints (SceneScout map data)
├── templates/
│   ├── public/          # Public-facing pages
│   ├── dashboard/        # Logged-in creator dashboard pages
│   ├── auth/             # Login/register/password reset
│   └── errors/           # 404 / 500 pages
├── static/
│   ├── images/uploads/   # Avatars, portfolio & location images
│   └── shelf_files/      # Uploaded digital shelf files
└── instance/
    └── creatora.db       # SQLite database (seeded with demo data — see below)
```

## Getting started

1. **Clone and install dependencies**

   ```bash
   git clone <this-repo-url>
   cd creatora
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**

   Copy `.env.example` to `.env` and set your own secret key:

   ```bash
   cp .env.example .env
   ```

   ```
   SECRET_KEY=your-super-secret-key-here
   DATABASE_URL=sqlite:///instance/creatora.db
   ```

3. **Database**

   This repo ships with a **pre-seeded SQLite database** (`instance/creatora.db`) so the app is fully populated out of the box — creator profiles, portfolios, locations, collabs, shelf items, testimonials, and more. No setup step is required to see it in action.

   If you'd rather start from a fresh/empty database, delete `instance/creatora.db`, then run:

   ```bash
   python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
   python seed.py
   ```

   `seed.py` is idempotent — it skips records that already exist, so it's safe to re-run at any time to top up demo data.

4. **Run the app**

   ```bash
   python app.py
   ```

   The app runs at `http://127.0.0.1:5000` by default.

## Demo accounts

All seeded creator accounts use the password:

```
Test1234!
```

A few to try (full list of 10+ in `seed.py`):

| Username    | Role               | Email                  |
|-------------|--------------------|------------------------|
| sofia_m     | Photographer       | sofia@creatora.com     |
| luca_v      | Videographer       | luca@creatora.com      |
| aria_k      | Digital artist     | aria@creatora.com      |
| marco_d     | Influencer         | marco@creatora.com     |
| elena_b     | Beauty creator     | elena@creatora.com     |
| nora_f      | Food creator       | nora@creatora.com      |
| dan_arch    | Architect          | dan@creatora.com       |
| zara_life   | Lifestyle creator  | zara@creatora.com      |

Log in with any of these, or register a brand new account from `/auth/register`.

## Notes

- File uploads (avatars, portfolio images, location photos, shelf files) are written to `static/images/uploads/` and `static/shelf_files/` and are included/created automatically as users upload content.
- The Digital Shelf checkout is a **simulation**, no real payment processor is integrated; "purchases" are logged to the `shelf_downloads` table with a fake payment reference.
