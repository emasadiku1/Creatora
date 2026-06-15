"""
Run this once to populate the DB with sample data.
Usage: python seed.py

Skips records that already exist, so safe to re-run.
"""
from app import app
from models import db, User, PortfolioItem, Collaboration, Location, ContentPost, Inquiry, Notification
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# ── Users ─────────────────────────────────────────────────────────────────────

SEED_USERS = [
    {"username": "sofia_m",     "email": "sofia@creatora.com",  "password": "Test1234!", "role": "photographer",      "display_name": "Sofia M.",  "bio": "Editorial & wedding photographer based in Tirana. Natural light, honest moments.",                  "location": "Tirana, Albania", "instagram": "@sofia.frames"},
    {"username": "luca_v",      "email": "luca@creatora.com",   "password": "Test1234!", "role": "videographer",      "display_name": "Luca V.",   "bio": "Cinematic storytelling for brands and events. Reels, fashion, commercial.",                         "location": "Tirana, Albania", "instagram": "@luca.lens"},
    {"username": "aria_k",      "email": "aria@creatora.com",   "password": "Test1234!", "role": "digital_artist",    "display_name": "Aria K.",   "bio": "Digital illustrator specializing in character design and brand identity.",                           "location": "Tirana, Albania", "instagram": "@aria.creates"},
    {"username": "marco_d",     "email": "marco@creatora.com",  "password": "Test1234!", "role": "influencer",        "display_name": "Marco D.",  "bio": "Lifestyle & travel content creator. 50K+ across platforms. Brand collabs open.",                    "location": "Tirana, Albania", "instagram": "@marco.daily"},
    {"username": "elena_b",     "email": "elena@creatora.com",  "password": "Test1234!", "role": "beauty_creator",    "display_name": "Elena B.",  "bio": "Beauty & lifestyle creator. Makeup tutorials, skincare routines, brand reviews.",                   "location": "Tirana, Albania", "instagram": "@elena.glam"},
    {"username": "nora_f",      "email": "nora@creatora.com",   "password": "Test1234!", "role": "food_creator",      "display_name": "Nora F.",   "bio": "Food photographer & recipe developer. Mediterranean flavors, honest cooking.",                      "location": "Tirana, Albania", "instagram": "@nora.kitchen"},
    {"username": "dan_arch",    "email": "dan@creatora.com",    "password": "Test1234!", "role": "architect",         "display_name": "Dan A.",    "bio": "Architect & visual storyteller. Residential projects, spatial design, 3D renders.",               "location": "Tirana, Albania", "instagram": "@dan.builds"},
    {"username": "mia_content", "email": "mia@creatora.com",    "password": "Test1234!", "role": "content_creator",  "display_name": "Mia C.",    "bio": "Short-form content creator across TikTok & Reels. Trend-driven, fast turnaround.",                "location": "Tirana, Albania", "instagram": "@mia.creates"},
    {"username": "zara_life",   "email": "zara@creatora.com",   "password": "Test1234!", "role": "lifestyle_creator", "display_name": "Zara L.",   "bio": "Lifestyle & wellness creator. Morning routines, travel diaries, slow living.",                     "location": "Tirana, Albania", "instagram": "@zara.life"},
    {"username": "alex_illus",  "email": "alex@creatora.com",   "password": "Test1234!", "role": "illustrator",       "display_name": "Alex I.",   "bio": "Illustrator for editorial, books, and brands. Bold lines, warm palettes.",                         "location": "Tirana, Albania", "instagram": "@alex.draws"},
]

# ── Locations ─────────────────────────────────────────────────────────────────
# (name, desc, category, vibe, lat, lng, best_time, crowd_level, owner_username)

SEED_LOCATIONS = [
    ("Rooftop Terrace",      "A stunning rooftop with panoramic city views, perfect for golden hour shoots.", "rooftop", "golden hour",  41.3275, 19.8187, "5pm–7pm",            "low",    "sofia_m"),
    ("Old Town Alley",       "Charming cobblestone alley in the old bazaar, full of texture and character.",  "urban",   "moody",        41.3289, 19.8203, "morning or overcast", "medium", "luca_v"),
    ("Lakeside Trail",       "Quiet trail along the lake with soft natural light and minimal foot traffic.",   "nature",  "soft & airy",  41.3150, 19.8050, "sunrise",            "low",    "sofia_m"),
    ("Bloom Café",           "Cozy café interior with warm tones, large windows and great espresso.",         "cafe",    "cozy",         41.3301, 19.8190, "morning",            "low",    "nora_f"),
    ("Abandoned Warehouse",  "Raw industrial space with dramatic light shafts — great for editorial shoots.", "industrial", "dramatic",  41.3220, 19.8140, "midday",             "low",    "luca_v"),
    ("Botanical Garden",     "Lush greenery and winding paths ideal for lifestyle and portrait sessions.",    "nature",  "fresh & green", 41.3340, 19.8250, "late morning",       "medium", "zara_life"),
    ("Grand Staircase",      "Monumental marble staircase at the Palace of Culture — iconic backdrop.",      "architecture", "cinematic", 41.3264, 19.8177, "golden hour",        "medium", "dan_arch"),
    ("Night Market Square",  "Vibrant square with string lights and food stalls — great for evening content.", "urban", "vibrant",      41.3280, 19.8195, "after 8pm",          "high",   "marco_d"),
]

# ── Collaborations ────────────────────────────────────────────────────────────
# (title, desc, role_needed, location, days_until_deadline, owner_username)

SEED_COLLABS = [
    ("Summer Campaign — Fashion Brand",     "Looking for a videographer to co-produce a 60-second brand film for a local fashion label. Budget confirmed.",             "videographer",      "Tirana",         14, "sofia_m"),
    ("Food Photography Collab",             "Teaming up with a restaurant for a full menu shoot. Need a stylist or second photographer for a half-day session.",       "photographer",      "Tirana",         10, "nora_f"),
    ("Travel Reel — Riviera Road Trip",     "Planning a 3-day content trip along the Albanian Riviera. Looking for a lifestyle creator or influencer to join.",        "lifestyle_creator", "Sarandë",        21, "marco_d"),
    ("Brand Identity for Studio Launch",    "Launching a creative studio and need a digital artist for logo, palette, and social kit. Paid project.",                  "digital_artist",    "Remote",          7, "dan_arch"),
    ("Beauty Tutorial Series",              "Collaborating with a cosmetics brand on a 4-part tutorial series. Seeking a videographer familiar with beauty content.",  "videographer",      "Tirana",         30, "elena_b"),
    ("Editorial Illustration — Magazine",   "Working with a local print magazine. Need an illustrator for 3 spreads — surreal, bold style preferred.",                 "illustrator",       "Tirana",         18, "aria_k"),
    ("Wellness Retreat Content Day",        "Shooting content for a wellness brand's summer retreat. Looking for a photographer with soft, natural style.",            "photographer",      "Vlorë",          12, "zara_life"),
    ("Short Film — 5-Minute Drama",         "Pre-production underway on a short film. Seeking a digital artist for title cards and poster design.",                    "digital_artist",    "Tirana",          9, "luca_v"),
]

# ── Content Posts ─────────────────────────────────────────────────────────────
# (title, platform, days_offset, status, notes, owner_username)
# days_offset: positive = future (scheduled), negative = past (published)

SEED_POSTS = [
    ("Golden Hour Rooftop Session",     "instagram", -5,  "published", "3 carousel images + caption. Performed well — 1.2K likes.", "sofia_m"),
    ("Wedding BTS Reel",                "instagram", -2,  "published", "30s behind-the-scenes reel from Saturday's wedding.",        "sofia_m"),
    ("Summer Collection Film",          "youtube",    3,  "scheduled", "Final cut ready. Schedule confirmed with brand.",            "luca_v"),
    ("Restaurant Menu Shoot Preview",   "instagram",  1,  "scheduled", "Teaser post before the full reveal next week.",             "nora_f"),
    ("Mediterranean Bowl Recipe",       "tiktok",    -1,  "published", "Recipe video — fastest to 10K views so far.",              "nora_f"),
    ("Morning Routine — Summer Edit",   "tiktok",     2,  "scheduled", "Voiceover recorded. B-roll needs trimming.",               "zara_life"),
    ("New Character Design Drop",       "instagram",  0,  "draft",     "Still finalising the colour palette variant.",             "aria_k"),
    ("Skincare Routine Collab",         "instagram",  4,  "scheduled", "Paid partnership post. Caption approved by brand.",        "elena_b"),
    ("City Architecture Walk",          "youtube",   -3,  "published", "Long-form walkthrough of the new boulevard project.",      "dan_arch"),
    ("Brand Identity Reveal",           "instagram",  6,  "scheduled", "Client approved final assets. Announce launch day.",       "dan_arch"),
    ("Riviera Road Trip Vlog Part 1",   "youtube",   -7,  "published", "Hit 5K views in the first 48 hours.",                     "marco_d"),
    ("5 Outfits 1 Destination",         "tiktok",     1,  "scheduled", "Trending audio queued. Need final cut review.",            "mia_content"),
    ("Editorial Spread — Issue 4",      "instagram",  5,  "scheduled", "Magazine drops Friday. Post embargoed until then.",        "alex_illus"),
    ("Illustration Process Video",      "tiktok",    -4,  "published", "Time-lapse of the new character from sketch to final.",    "alex_illus"),
]

# ── Inquiries ─────────────────────────────────────────────────────────────────
# (sender_name, sender_email, message, status, days_ago, owner_username)

SEED_INQUIRIES = [
    ("Olta Hoxha",     "olta@bloom.al",      "Hi Sofia! We'd love to book you for our café's rebrand shoot next month. Do you have availability in July?",          "discussion", 3, "sofia_m"),
    ("Gent Basha",     "gent@studiob.al",    "Interested in a 2-hour portrait session for my acting portfolio. Can you share your packages?",                       "new",        1, "sofia_m"),
    ("Rinor Dema",     "rinor@pulse.al",     "We're producing a product launch video and need a videographer for a full day. Budget is €600. Interested?",         "booked",     6, "luca_v"),
    ("Fatma Shehu",    "fatma@bloom.al",     "Love your food content, Nora! Would you be open to developing 5 recipes for our summer menu campaign?",              "discussion", 2, "nora_f"),
    ("Brand Team",     "hello@cosmica.al",   "We'd like to send you our new summer collection for an honest review. Let us know if you're interested!",            "new",        0, "elena_b"),
    ("Dritan Çela",    "dritan@archstudio.al","Saw your Boulevard walkthrough — impressive work. Could we discuss a collaboration on our new residential project?", "new",        1, "dan_arch"),
    ("Lira Mema",      "lira@yogahouse.al",  "We're hosting a wellness retreat in Vlorë and would love a content creator to document the experience. Paid gig.",   "discussion", 4, "zara_life"),
    ("Enis Kola",      "enis@inkpress.al",   "We're a local magazine looking for an illustrator for our autumn issue. 3 full-page spreads. Are you available?",    "booked",     8, "alex_illus"),
    ("Marta Gjoka",    "marta@mgjoka.com",   "Hi Marco! We'd love to have you join our Riviera trip as a brand ambassador. Full expenses covered.",                "completed",  15, "marco_d"),
    ("Studio Nine",    "hello@studionine.al","Mia, we spotted your TikToks and would love to brief you on a campaign for our new café concept. Thoughts?",         "new",        0, "mia_content"),
]

# ── Notifications ─────────────────────────────────────────────────────────────
# (type, title, message, link, is_read, days_ago, owner_username)

SEED_NOTIFICATIONS = [
    ("inquiry", "New inquiry from Olta Hoxha",   "Olta sent you a booking request for a café rebrand shoot.",          "/dashboard/crm",      False, 3,  "sofia_m"),
    ("inquiry", "Rinor Dema confirmed booking",  "Your session with Rinor Dema is now booked.",                        "/dashboard/crm",      True,  6,  "luca_v"),
    ("collab",  "New collab application",        "Someone applied to your Summer Campaign collab post.",               "/dashboard/my_collabs", False, 1, "sofia_m"),
    ("system",  "Welcome to Creatora!",          "Your profile is live. Complete your portfolio to attract clients.",  "/dashboard/portfolio", True, 30, "sofia_m"),
    ("system",  "Welcome to Creatora!",          "Your profile is live. Complete your portfolio to attract clients.",  "/dashboard/portfolio", True, 30, "luca_v"),
    ("system",  "Welcome to Creatora!",          "Your profile is live. Complete your portfolio to attract clients.",  "/dashboard/portfolio", True, 30, "nora_f"),
    ("inquiry", "New inquiry from Brand Team",   "Cosmica wants to send you their summer collection for review.",      "/dashboard/crm",      False, 0,  "elena_b"),
    ("collab",  "Collab deadline approaching",   "Your 'Short Film' collab post closes in 9 days.",                   "/dashboard/my_collabs", False, 1, "luca_v"),
    ("inquiry", "Inquiry marked as completed",   "Your project with Marta Gjoka has been marked complete.",           "/dashboard/crm",      True,  15, "marco_d"),
    ("system",  "Profile view milestone",        "Your profile has been viewed 100 times this month!",               "/dashboard/analytics", False, 2, "marco_d"),
]


# ── Seed function ─────────────────────────────────────────────────────────────

def seed():
    with app.app_context():
        now = datetime.utcnow()

        # ── Users & portfolio items ──
        user_map = {}  # username -> User object
        for u in SEED_USERS:
            existing = User.query.filter_by(email=u["email"]).first()
            if existing:
                user_map[u["username"]] = existing
                print(f"  ⚠️  Skipping user {u['display_name']} — already exists")
                continue

            user = User(
                username=u["username"], email=u["email"],
                password=generate_password_hash(u["password"]),
                role=u["role"], display_name=u["display_name"],
                bio=u["bio"], location=u["location"],
                instagram=u["instagram"], is_public=True,
            )
            db.session.add(user)
            db.session.flush()
            user_map[u["username"]] = user

            for i in range(1, 3):
                db.session.add(PortfolioItem(
                    creator_id=user.id,
                    title=f"{u['display_name']} — Project {i}",
                    description=f"Sample project {i} by {u['display_name']}.",
                    category=u["role"], is_featured=(i == 1),
                ))
            print(f"  ✓  Added user {u['display_name']} ({u['role']})")

        db.session.flush()

        # ── Locations ──
        for name, desc, cat, vibe, lat, lng, best_time, crowd, owner in SEED_LOCATIONS:
            if Location.query.filter_by(name=name).first():
                print(f"  ⚠️  Skipping location '{name}' — already exists")
                continue
            owner_user = user_map.get(owner) or User.query.filter_by(username=owner).first()
            if not owner_user:
                continue
            db.session.add(Location(
                creator_id=owner_user.id, name=name, description=desc,
                category=cat, vibe=vibe, lat=lat, lng=lng,
                best_time=best_time, crowd_level=crowd,
            ))
            print(f"  📍 Added location: {name}")

        # ── Collaborations ──
        for title, desc, role_needed, location, days, owner in SEED_COLLABS:
            if Collaboration.query.filter_by(title=title).first():
                print(f"  ⚠️  Skipping collab '{title}' — already exists")
                continue
            owner_user = user_map.get(owner) or User.query.filter_by(username=owner).first()
            if not owner_user:
                continue
            db.session.add(Collaboration(
                creator_id=owner_user.id, title=title, description=desc,
                role_needed=role_needed, location=location,
                deadline=now + timedelta(days=days), is_open=True,
            ))
            print(f"  🤝 Added collab: {title}")

        # ── Content posts ──
        for title, platform, day_offset, status, notes, owner in SEED_POSTS:
            if ContentPost.query.filter_by(title=title).first():
                print(f"  ⚠️  Skipping post '{title}' — already exists")
                continue
            owner_user = user_map.get(owner) or User.query.filter_by(username=owner).first()
            if not owner_user:
                continue
            scheduled_dt = now + timedelta(days=day_offset) if day_offset != 0 else now
            db.session.add(ContentPost(
                creator_id=owner_user.id, title=title, platform=platform,
                scheduled=scheduled_dt, status=status, notes=notes,
            ))
            print(f"  📅 Added post: {title}")

        # ── Inquiries ──
        for sender_name, sender_email, message, status, days_ago, owner in SEED_INQUIRIES:
            if Inquiry.query.filter_by(email=sender_email, creator_id=None).first() is not None:
                pass  # can't reliably check without creator_id, just try to add
            owner_user = user_map.get(owner) or User.query.filter_by(username=owner).first()
            if not owner_user:
                continue
            already = Inquiry.query.filter_by(email=sender_email, creator_id=owner_user.id).first()
            if already:
                print(f"  ⚠️  Skipping inquiry from {sender_name} — already exists")
                continue
            inq = Inquiry(
                creator_id=owner_user.id, name=sender_name,
                email=sender_email, message=message, status=status,
                created_at=now - timedelta(days=days_ago),
            )
            db.session.add(inq)
            print(f"  📩 Added inquiry from {sender_name} → {owner}")

        # ── Notifications ──
        for ntype, title, message, link, is_read, days_ago, owner in SEED_NOTIFICATIONS:
            owner_user = user_map.get(owner) or User.query.filter_by(username=owner).first()
            if not owner_user:
                continue
            already = Notification.query.filter_by(title=title, user_id=owner_user.id).first()
            if already:
                print(f"  ⚠️  Skipping notification '{title}' — already exists")
                continue
            db.session.add(Notification(
                user_id=owner_user.id, type=ntype, title=title,
                message=message, link=link, is_read=is_read,
                created_at=now - timedelta(days=days_ago),
            ))
            print(f"  🔔 Added notification: {title} → {owner}")

        db.session.commit()
        print("\n✅ Seed complete!")

if __name__ == "__main__":
    seed()