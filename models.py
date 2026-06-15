from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ── Creator roles ─────────────────────────────────────────────────────────────
CREATOR_ROLES = [
    'photographer',
    'videographer',
    'digital_artist',
    'illustrator',
    'architect',
    'influencer',
    'content_creator',
    'beauty_creator',
    'lifestyle_creator',
    'food_creator',
]


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(50),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(256), nullable=False)
    role         = db.Column(db.String(30),  nullable=False)  # one of CREATOR_ROLES

    # Profile
    display_name  = db.Column(db.String(100))
    bio           = db.Column(db.Text)
    location      = db.Column(db.String(100))
    avatar        = db.Column(db.String(255))   # filename in uploads/
    website       = db.Column(db.String(255))
    instagram     = db.Column(db.String(100))
    is_public     = db.Column(db.Boolean, default=True)
    security_question = db.Column(db.String(255))  # ← add
    security_answer = db.Column(db.String(255))  # ← add (stored hashed)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    portfolio_items = db.relationship('PortfolioItem',  backref='creator', lazy=True)
    inquiries_recv  = db.relationship('Inquiry',        backref='creator', lazy=True,
                                      foreign_keys='Inquiry.creator_id')
    content_posts   = db.relationship('ContentPost',    backref='creator', lazy=True)
    locations       = db.relationship('Location',       backref='creator', lazy=True)
    collaborations  = db.relationship('Collaboration',  backref='creator', lazy=True)
    shelf_items = db.relationship('ShelfItem', backref='creator', lazy=True)

    is_public = db.Column(db.Boolean, default=True)
    profile_views = db.Column(db.Integer, default=0)  # ← add this

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'

    id          = db.Column(db.Integer, primary_key=True)
    creator_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    image       = db.Column(db.String(255))
    category    = db.Column(db.String(60))
    is_featured = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Inquiry(db.Model):
    __tablename__ = 'inquiries'

    id          = db.Column(db.Integer, primary_key=True)
    creator_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(120), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    status      = db.Column(db.String(20), default='new')   # new | discussion | booked | completed
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class ContentPost(db.Model):
    __tablename__ = 'content_posts'

    id          = db.Column(db.Integer, primary_key=True)
    creator_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title       = db.Column(db.String(120))
    platform    = db.Column(db.String(30))   # instagram | tiktok | youtube | other
    scheduled   = db.Column(db.DateTime)
    status      = db.Column(db.String(20), default='draft')  # draft | scheduled | published
    notes       = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Location(db.Model):
    __tablename__ = 'locations'

    id          = db.Column(db.Integer, primary_key=True)
    creator_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name        = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category    = db.Column(db.String(60))   # rooftop | cafe | nature | urban | etc.
    vibe        = db.Column(db.String(60))
    lat         = db.Column(db.Float)
    lng         = db.Column(db.Float)
    best_time   = db.Column(db.String(100))
    crowd_level = db.Column(db.String(20))   # low | medium | high
    image       = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Collaboration(db.Model):
    __tablename__ = 'collaborations'

    id           = db.Column(db.Integer, primary_key=True)
    creator_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title        = db.Column(db.String(120), nullable=False)
    description  = db.Column(db.Text)
    role_needed  = db.Column(db.String(60))
    location     = db.Column(db.String(100))
    deadline     = db.Column(db.DateTime)
    is_open      = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type       = db.Column(db.String(30), nullable=False)   # inquiry | collab | system
    title      = db.Column(db.String(120), nullable=False)
    message    = db.Column(db.String(255))
    link       = db.Column(db.String(255))                  # relative URL to navigate to
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))


# ── Digital Shelf ─────────────────────────────────────────────────────────────

SHELF_CATEGORIES = [
    'preset',  # Lightroom, Capture One presets
    'template',  # PSD, Canva, Notion templates
    'lut',  # Video LUTs
    'guide',  # PDF guides, e-books
    'font',  # Font files
    'brush',  # Photoshop/Procreate brushes
    'overlay',  # Photo overlays, textures
    'other',
]


class ShelfItem(db.Model):
    __tablename__ = 'shelf_items'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Listing info
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(30))  # from SHELF_CATEGORIES
    cover_image = db.Column(db.String(255))  # preview image filename
    tags = db.Column(db.String(255))  # comma-separated

    # File
    file_path = db.Column(db.String(255), nullable=False)  # stored filename
    file_name = db.Column(db.String(255))  # original filename shown to buyer
    file_size = db.Column(db.Integer)  # bytes
    file_type = db.Column(db.String(50))  # e.g. "zip", "pdf", "xmp"

    # Pricing
    price = db.Column(db.Float, default=0.0)  # 0.0 = free
    currency = db.Column(db.String(3), default='USD')
    is_free = db.Column(db.Boolean, default=False)

    # Status
    is_published = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    downloads = db.relationship('ShelfDownload', backref='item', lazy=True)


class ShelfDownload(db.Model):
    """Tracks every download — for free items and paid purchases alike."""
    __tablename__ = 'shelf_downloads'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('shelf_items.id'), nullable=False)

    # buyer_id is nullable — free items can be downloaded without an account
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    buyer_email = db.Column(db.String(120))  # captured even for guests

    # Payment (null if free)
    amount_paid = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    payment_ref = db.Column(db.String(100), nullable=True)  # Stripe charge ID etc.

    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # for abuse prevention

class Testimonial(db.Model):
    """Client-submitted testimonials for a creator's public profile."""
    __tablename__ = 'testimonials'

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Submitter info (no account required)
    author_name  = db.Column(db.String(120), nullable=False)
    author_title = db.Column(db.String(120))   # e.g. "Marketing Director at Acme"
    author_email = db.Column(db.String(120))   # kept private, not shown publicly

    # Content
    body   = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)  # 1-5 stars

    # Moderation
    is_approved = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to creator
    creator = db.relationship('User', backref=db.backref('testimonials', lazy=True))

# ── Services & Pricing ────────────────────────────────────────────────────────

class Service(db.Model):
    """A service offering shown on the creator's public profile."""
    __tablename__ = 'services'

    id          = db.Column(db.Integer, primary_key=True)
    creator_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title       = db.Column(db.String(120), nullable=False)   # e.g. "Brand Photography"
    description = db.Column(db.Text)
    price_from  = db.Column(db.Float)                         # starting price (nullable = "contact for pricing")
    price_to    = db.Column(db.Float)                         # upper range (nullable = single price)
    currency    = db.Column(db.String(3), default='USD')
    unit        = db.Column(db.String(40))                    # e.g. "per session", "per day", "per project"
    is_featured = db.Column(db.Boolean, default=False)
    sort_order  = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', backref=db.backref('services', lazy=True))