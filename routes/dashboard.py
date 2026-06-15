from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask_login import login_required, current_user, logout_user
from models import PortfolioItem, Inquiry, ContentPost, Location, Collaboration, User, Notification, ShelfItem, db
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os

dashboard_bp = Blueprint('dashboard', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Home ──────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/')
@login_required
def home():
    pending_inquiries = Inquiry.query.filter_by(
        creator_id=current_user.id, status='new'
    ).count()
    recent_inquiries = Inquiry.query.filter_by(
        creator_id=current_user.id
    ).order_by(Inquiry.created_at.desc()).limit(5).all()
    portfolio_count = PortfolioItem.query.filter_by(creator_id=current_user.id).count()
    active_collabs = Collaboration.query.filter_by(
        creator_id=current_user.id, is_open=True
    ).count()
    my_collabs = Collaboration.query.filter_by(
        creator_id=current_user.id
    ).order_by(Collaboration.created_at.desc()).limit(4).all()
    upcoming_posts = ContentPost.query.filter(
        ContentPost.creator_id == current_user.id,
        ContentPost.status == 'scheduled',
        ContentPost.scheduled >= datetime.utcnow()
    ).count()
    upcoming_content = ContentPost.query.filter(
        ContentPost.creator_id == current_user.id,
        ContentPost.status.in_(['scheduled', 'draft'])
    ).order_by(ContentPost.scheduled.asc()).limit(5).all()

    shelf_items     = ShelfItem.query.filter_by(creator_id=current_user.id, is_published=True).all()
    shelf_count     = len(shelf_items)
    shelf_downloads = sum(i.download_count for i in shelf_items)

    return render_template(
        'dashboard/home.html',
        pending_inquiries=pending_inquiries,
        recent_inquiries=recent_inquiries,
        portfolio_count=portfolio_count,
        active_collabs=active_collabs,
        my_collabs=my_collabs,
        upcoming_posts=upcoming_posts,
        upcoming_content=upcoming_content,
        shelf_count=shelf_count,
        shelf_downloads=shelf_downloads,
    )


# ── Portfolio ─────────────────────────────────────────────────────────────────

@dashboard_bp.route('/portfolio')
@login_required
def portfolio():
    items = PortfolioItem.query.filter_by(
        creator_id=current_user.id
    ).order_by(PortfolioItem.created_at.desc()).all()
    return render_template('dashboard/portfolio.html', items=items)


@dashboard_bp.route('/portfolio/add', methods=['POST'])
@login_required
def add_portfolio_item():
    title    = request.form.get('title', '').strip()
    category = request.form.get('category', '').strip()
    desc     = request.form.get('description', '').strip()
    featured = bool(request.form.get('is_featured'))
    image_filename = None

    file = request.files.get('image')
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(save_path)
        image_filename = filename

    item = PortfolioItem(
        creator_id=current_user.id,
        title=title,
        description=desc or None,
        category=category or None,
        image=image_filename,
        is_featured=featured,
    )
    db.session.add(item)
    db.session.commit()
    flash('Portfolio item added!', 'success')
    return redirect(url_for('dashboard.portfolio'))


@dashboard_bp.route('/portfolio/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_portfolio_item(item_id):
    item = PortfolioItem.query.filter_by(id=item_id, creator_id=current_user.id).first_or_404()
    item.title       = request.form.get('title', item.title).strip()
    item.category    = request.form.get('category', '').strip() or None
    item.description = request.form.get('description', '').strip() or None
    item.is_featured = bool(request.form.get('is_featured'))

    file = request.files.get('image')
    if file and allowed_file(file.filename):
        filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(save_path)
        item.image = filename

    db.session.commit()
    flash('Portfolio item updated!', 'success')
    return redirect(url_for('dashboard.portfolio'))


@dashboard_bp.route('/portfolio/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_portfolio_item(item_id):
    item = PortfolioItem.query.filter_by(id=item_id, creator_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Portfolio item deleted.', 'info')
    return redirect(url_for('dashboard.portfolio'))


# ── Client CRM ────────────────────────────────────────────────────────────────

@dashboard_bp.route('/crm')
@login_required
def crm():
    status = request.args.get('status', '')
    query  = Inquiry.query.filter_by(creator_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    inquiries = query.order_by(Inquiry.created_at.desc()).all()
    counts = {
        'new':        Inquiry.query.filter_by(creator_id=current_user.id, status='new').count(),
        'discussion': Inquiry.query.filter_by(creator_id=current_user.id, status='discussion').count(),
        'booked':     Inquiry.query.filter_by(creator_id=current_user.id, status='booked').count(),
        'completed':  Inquiry.query.filter_by(creator_id=current_user.id, status='completed').count(),
    }
    return render_template('dashboard/crm.html', inquiries=inquiries, counts=counts, active_status=status)


@dashboard_bp.route('/crm/<int:inquiry_id>/status', methods=['POST'])
@login_required
def update_inquiry_status(inquiry_id):
    inquiry = Inquiry.query.filter_by(id=inquiry_id, creator_id=current_user.id).first_or_404()
    new_status = request.form.get('status')
    if new_status in ('new', 'discussion', 'booked', 'completed'):
        inquiry.status = new_status
        db.session.commit()
    return redirect(url_for('dashboard.crm'))


# ── Content Planner ───────────────────────────────────────────────────────────

@dashboard_bp.route('/planner')
@login_required
def planner():
    posts = ContentPost.query.filter_by(
        creator_id=current_user.id
    ).order_by(ContentPost.scheduled.asc()).all()
    return render_template('dashboard/planner.html', posts=posts)


@dashboard_bp.route('/planner/add', methods=['POST'])
@login_required
def add_post():
    scheduled_str = request.form.get('scheduled')
    scheduled = datetime.strptime(scheduled_str, '%Y-%m-%dT%H:%M') if scheduled_str else None
    post = ContentPost(
        creator_id=current_user.id,
        title=request.form.get('title', '').strip() or None,
        platform=request.form.get('platform') or None,
        scheduled=scheduled,
        status=request.form.get('status', 'draft'),
        notes=request.form.get('notes', '').strip() or None,
    )
    db.session.add(post)
    db.session.commit()
    flash('Post added to planner!', 'success')
    return redirect(url_for('dashboard.planner'))


@dashboard_bp.route('/planner/<int:post_id>/edit', methods=['POST'])
@login_required
def edit_post(post_id):
    post = ContentPost.query.filter_by(id=post_id, creator_id=current_user.id).first_or_404()
    scheduled_str = request.form.get('scheduled')
    post.title     = request.form.get('title', '').strip() or None
    post.platform  = request.form.get('platform') or None
    post.status    = request.form.get('status', 'draft')
    post.notes     = request.form.get('notes', '').strip() or None
    post.scheduled = datetime.strptime(scheduled_str, '%Y-%m-%dT%H:%M') if scheduled_str else None
    db.session.commit()
    flash('Post updated!', 'success')
    return redirect(url_for('dashboard.planner'))


@dashboard_bp.route('/planner/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = ContentPost.query.filter_by(id=post_id, creator_id=current_user.id).first_or_404()
    db.session.delete(post)
    db.session.commit()
    flash('Post removed.', 'info')
    return redirect(url_for('dashboard.planner'))


# ── My Collabs ────────────────────────────────────────────────────────────────

@dashboard_bp.route('/collabs/my')
@login_required
def my_collabs():
    collabs = Collaboration.query.filter_by(
        creator_id=current_user.id
    ).order_by(Collaboration.created_at.desc()).all()
    return render_template('dashboard/my_collabs.html', collabs=collabs)


@dashboard_bp.route('/collabs/<int:collab_id>/edit', methods=['POST'])
@login_required
def edit_collab(collab_id):
    collab = Collaboration.query.filter_by(id=collab_id, creator_id=current_user.id).first_or_404()
    deadline_str = request.form.get('deadline')
    collab.title       = request.form.get('title', collab.title).strip()
    collab.description = request.form.get('description', '').strip() or None
    collab.role_needed = request.form.get('role_needed') or None
    collab.location    = request.form.get('location', '').strip() or None
    collab.deadline    = datetime.strptime(deadline_str, '%Y-%m-%d') if deadline_str else None
    db.session.commit()
    flash('Collab updated!', 'success')
    return redirect(url_for('dashboard.my_collabs'))


@dashboard_bp.route('/collabs/<int:collab_id>/toggle', methods=['POST'])
@login_required
def toggle_collab(collab_id):
    collab = Collaboration.query.filter_by(id=collab_id, creator_id=current_user.id).first_or_404()
    collab.is_open = not collab.is_open
    db.session.commit()
    flash('Collab updated.', 'success')
    return redirect(url_for('dashboard.my_collabs'))


@dashboard_bp.route('/collabs/<int:collab_id>/delete', methods=['POST'])
@login_required
def delete_collab(collab_id):
    collab = Collaboration.query.filter_by(id=collab_id, creator_id=current_user.id).first_or_404()
    db.session.delete(collab)
    db.session.commit()
    flash('Collab deleted.', 'info')
    return redirect(url_for('dashboard.my_collabs'))


# ── SceneScout (my locations) ─────────────────────────────────────────────────

@dashboard_bp.route('/scenescout/my')
@login_required
def my_locations():
    locations = Location.query.filter_by(
        creator_id=current_user.id
    ).order_by(Location.created_at.desc()).all()
    return render_template('dashboard/my_locations.html', locations=locations)


@dashboard_bp.route('/scenescout/add', methods=['POST'])
@login_required
def add_location():
    image_filename = None
    file = request.files.get('image')
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(save_path)
        image_filename = filename

    location = Location(
        creator_id=current_user.id,
        name=request.form.get('name', '').strip(),
        description=request.form.get('description', '').strip() or None,
        category=request.form.get('category') or None,
        vibe=request.form.get('vibe', '').strip() or None,
        best_time=request.form.get('best_time', '').strip() or None,
        crowd_level=request.form.get('crowd_level') or None,
        lat=request.form.get('lat', type=float),
        lng=request.form.get('lng', type=float),
        image=image_filename,
    )
    db.session.add(location)
    db.session.commit()
    flash('Location added to SceneScout!', 'success')
    return redirect(url_for('dashboard.my_locations'))


@dashboard_bp.route('/scenescout/<int:location_id>/edit', methods=['POST'])
@login_required
def edit_location(location_id):
    loc = Location.query.filter_by(id=location_id, creator_id=current_user.id).first_or_404()
    loc.name        = request.form.get('name', '').strip() or loc.name
    loc.description = request.form.get('description', '').strip() or None
    loc.category    = request.form.get('category') or None
    loc.vibe        = request.form.get('vibe', '').strip() or None
    loc.best_time   = request.form.get('best_time', '').strip() or None
    loc.crowd_level = request.form.get('crowd_level') or None

    lat_raw = request.form.get('lat', '').strip()
    lng_raw = request.form.get('lng', '').strip()
    if lat_raw and lng_raw:
        try:
            loc.lat = float(lat_raw)
            loc.lng = float(lng_raw)
        except ValueError:
            pass

    file = request.files.get('image')
    if file and allowed_file(file.filename):
        filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(save_path)
        loc.image = filename

    db.session.commit()
    flash('Location updated!', 'success')
    return redirect(url_for('dashboard.my_locations'))


@dashboard_bp.route('/scenescout/<int:location_id>/delete', methods=['POST'])
@login_required
def delete_location(location_id):
    loc = Location.query.filter_by(id=location_id, creator_id=current_user.id).first_or_404()
    db.session.delete(loc)
    db.session.commit()
    flash('Location removed.', 'info')
    return redirect(url_for('dashboard.my_locations'))


# ── Analytics ─────────────────────────────────────────────────────────────────

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    uid = current_user.id

    # ── Portfolio ──
    portfolio_count   = PortfolioItem.query.filter_by(creator_id=uid).count()
    featured_count    = PortfolioItem.query.filter_by(creator_id=uid, is_featured=True).count()

    # ── Inquiries ──
    total_inquiries   = Inquiry.query.filter_by(creator_id=uid).count()
    new_count         = Inquiry.query.filter_by(creator_id=uid, status='new').count()
    discussion_count  = Inquiry.query.filter_by(creator_id=uid, status='discussion').count()
    booked_count      = Inquiry.query.filter_by(creator_id=uid, status='booked').count()
    completed_count   = Inquiry.query.filter_by(creator_id=uid, status='completed').count()
    conversion_rate   = round((booked_count / total_inquiries * 100)) if total_inquiries else 0

    # ── Content ──
    total_posts       = ContentPost.query.filter_by(creator_id=uid).count()
    scheduled_posts   = ContentPost.query.filter_by(creator_id=uid, status='scheduled').count()
    published_posts   = ContentPost.query.filter_by(creator_id=uid, status='published').count()
    draft_posts       = ContentPost.query.filter_by(creator_id=uid, status='draft').count()

    # Posts by platform
    from sqlalchemy import func
    platform_counts_raw = (
        db.session.query(ContentPost.platform, func.count(ContentPost.id))
        .filter(ContentPost.creator_id == uid, ContentPost.platform != None)
        .group_by(ContentPost.platform)
        .all()
    )
    platform_counts = {p: c for p, c in platform_counts_raw}

    # ── Collabs ──
    total_collabs     = Collaboration.query.filter_by(creator_id=uid).count()
    active_collabs    = Collaboration.query.filter_by(creator_id=uid, is_open=True).count()
    closed_collabs    = Collaboration.query.filter_by(creator_id=uid, is_open=False).count()

    # ── Locations ──
    total_locations   = Location.query.filter_by(creator_id=uid).count()

    # ── Recent inquiries (last 6) for mini list ──
    recent_inquiries  = Inquiry.query.filter_by(creator_id=uid).order_by(Inquiry.created_at.desc()).limit(6).all()

    profile_views = current_user.profile_views or 0

    return render_template(
        'dashboard/analytics.html',
        # portfolio
        portfolio_count=portfolio_count,
        featured_count=featured_count,
        # inquiries
        total_inquiries=total_inquiries,
        new_count=new_count,
        discussion_count=discussion_count,
        booked_count=booked_count,
        completed_count=completed_count,
        conversion_rate=conversion_rate,
        recent_inquiries=recent_inquiries,
        # content
        total_posts=total_posts,
        scheduled_posts=scheduled_posts,
        published_posts=published_posts,
        draft_posts=draft_posts,
        platform_counts=platform_counts,
        # collabs
        total_collabs=total_collabs,
        active_collabs=active_collabs,
        closed_collabs=closed_collabs,
        # locations
        total_locations=total_locations,
        profile_views=profile_views
    )


# ── Settings ──────────────────────────────────────────────────────────────────

@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.display_name = request.form.get('display_name', '').strip() or None
        current_user.bio          = request.form.get('bio', '').strip() or None
        current_user.location     = request.form.get('location', '').strip() or None
        current_user.website      = request.form.get('website', '').strip() or None
        current_user.instagram    = request.form.get('instagram', '').strip() or None
        current_user.is_public    = bool(request.form.get('is_public'))

        # Security question
        sq = request.form.get('security_question', '').strip()
        sa = request.form.get('security_answer', '').strip().lower()
        if sq and sa:
            current_user.security_question = sq
            current_user.security_answer = generate_password_hash(sa)
        file = request.files.get('avatar')

        if file and allowed_file(file.filename):
            filename = f"{current_user.id}_avatar_{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(save_path)
            current_user.avatar = filename

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('dashboard.settings'))

    return render_template('dashboard/settings.html')


@dashboard_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('dashboard.settings') + '#account')
    if len(new_password) < 8:
        flash('New password must be at least 8 characters.', 'danger')
        return redirect(url_for('dashboard.settings') + '#account')
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('dashboard.settings') + '#account')

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated.', 'success')
    return redirect(url_for('dashboard.settings') + '#account')


@dashboard_bp.route('/settings/export')
@login_required
def export_account_data():
    from models import Service, Testimonial, ShelfDownload

    uid = current_user.id
    shelf_items = ShelfItem.query.filter_by(creator_id=uid).all()
    shelf_ids = [item.id for item in shelf_items]
    data = {
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'role': current_user.role,
            'display_name': current_user.display_name,
            'bio': current_user.bio,
            'location': current_user.location,
            'website': current_user.website,
            'instagram': current_user.instagram,
            'is_public': current_user.is_public,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        },
        'portfolio_items': [
            {
                'title': item.title,
                'description': item.description,
                'category': item.category,
                'image': item.image,
                'is_featured': item.is_featured,
                'created_at': item.created_at.isoformat() if item.created_at else None,
            }
            for item in PortfolioItem.query.filter_by(creator_id=uid).all()
        ],
        'inquiries': [
            {
                'name': inquiry.name,
                'email': inquiry.email,
                'message': inquiry.message,
                'status': inquiry.status,
                'created_at': inquiry.created_at.isoformat() if inquiry.created_at else None,
            }
            for inquiry in Inquiry.query.filter_by(creator_id=uid).all()
        ],
        'content_posts': [
            {
                'title': post.title,
                'platform': post.platform,
                'scheduled': post.scheduled.isoformat() if post.scheduled else None,
                'status': post.status,
                'notes': post.notes,
                'created_at': post.created_at.isoformat() if post.created_at else None,
            }
            for post in ContentPost.query.filter_by(creator_id=uid).all()
        ],
        'locations': [
            {
                'name': loc.name,
                'description': loc.description,
                'category': loc.category,
                'vibe': loc.vibe,
                'lat': loc.lat,
                'lng': loc.lng,
                'best_time': loc.best_time,
                'crowd_level': loc.crowd_level,
                'image': loc.image,
                'created_at': loc.created_at.isoformat() if loc.created_at else None,
            }
            for loc in Location.query.filter_by(creator_id=uid).all()
        ],
        'collaborations': [
            {
                'title': collab.title,
                'description': collab.description,
                'role_needed': collab.role_needed,
                'location': collab.location,
                'deadline': collab.deadline.isoformat() if collab.deadline else None,
                'is_open': collab.is_open,
                'created_at': collab.created_at.isoformat() if collab.created_at else None,
            }
            for collab in Collaboration.query.filter_by(creator_id=uid).all()
        ],
        'shelf_items': [
            {
                'title': item.title,
                'description': item.description,
                'category': item.category,
                'tags': item.tags,
                'price': item.price,
                'currency': item.currency,
                'is_free': item.is_free,
                'is_published': item.is_published,
                'download_count': item.download_count,
                'file_name': item.file_name,
                'created_at': item.created_at.isoformat() if item.created_at else None,
            }
            for item in shelf_items
        ],
        'shelf_downloads': [
            {
                'item_id': download.item_id,
                'buyer_email': download.buyer_email,
                'amount_paid': download.amount_paid,
                'currency': download.currency,
                'downloaded_at': download.downloaded_at.isoformat() if download.downloaded_at else None,
            }
            for download in ShelfDownload.query.filter(ShelfDownload.item_id.in_(shelf_ids)).all()
        ] if shelf_ids else [],
        'services': [
            {
                'title': service.title,
                'description': service.description,
                'price_from': service.price_from,
                'price_to': service.price_to,
                'currency': service.currency,
                'unit': service.unit,
                'is_featured': service.is_featured,
                'created_at': service.created_at.isoformat() if service.created_at else None,
            }
            for service in Service.query.filter_by(creator_id=uid).all()
        ],
        'testimonials': [
            {
                'author_name': testimonial.author_name,
                'author_title': testimonial.author_title,
                'author_email': testimonial.author_email,
                'body': testimonial.body,
                'rating': testimonial.rating,
                'is_approved': testimonial.is_approved,
                'created_at': testimonial.created_at.isoformat() if testimonial.created_at else None,
            }
            for testimonial in Testimonial.query.filter_by(creator_id=uid).all()
        ],
    }
    payload = json.dumps(data, indent=2)
    return Response(
        payload,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=creatora-{current_user.username}-export.json'},
    )


@dashboard_bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    from models import Service, Testimonial, ShelfDownload

    username_confirm = request.form.get('username_confirm', '').strip()
    password = request.form.get('password', '')
    if username_confirm != current_user.username:
        flash('Type your username to confirm account deletion.', 'danger')
        return redirect(url_for('dashboard.settings') + '#account')
    if not check_password_hash(current_user.password, password):
        flash('Password is incorrect.', 'danger')
        return redirect(url_for('dashboard.settings') + '#account')

    uid = current_user.id
    user = User.query.get(uid)
    shelf_ids = [item.id for item in ShelfItem.query.filter_by(creator_id=uid).all()]
    if shelf_ids:
        ShelfDownload.query.filter(ShelfDownload.item_id.in_(shelf_ids)).delete(synchronize_session=False)
    ShelfDownload.query.filter_by(buyer_id=uid).update({'buyer_id': None}, synchronize_session=False)
    Notification.query.filter_by(user_id=uid).delete()
    Testimonial.query.filter_by(creator_id=uid).delete()
    Service.query.filter_by(creator_id=uid).delete()
    ShelfItem.query.filter_by(creator_id=uid).delete()
    Collaboration.query.filter_by(creator_id=uid).delete()
    Location.query.filter_by(creator_id=uid).delete()
    ContentPost.query.filter_by(creator_id=uid).delete()
    Inquiry.query.filter_by(creator_id=uid).delete()
    PortfolioItem.query.filter_by(creator_id=uid).delete()
    db.session.delete(user)
    db.session.commit()
    logout_user()
    flash('Your account and creator data have been deleted.', 'info')
    return redirect(url_for('public.index'))

# ── Notifications ─────────────────────────────────────────────────────────────

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    # mark all as read when the page is opened
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('dashboard/notifications.html', notifications=notifs)


@dashboard_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for('dashboard.notifications'))


@dashboard_bp.route('/notifications/clear', methods=['POST'])
@login_required
def clear_notifications():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('All notifications cleared.', 'info')
    return redirect(url_for('dashboard.notifications'))


# ── Shelf ─────────────────────────────────────────────────────────────────────

SHELF_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'shelf_files')
SHELF_ALLOWED_EXTENSIONS = {'zip', 'pdf', 'xmp', 'cube', 'png', 'jpg', 'jpeg', 'ttf', 'otf', 'abr'}

def allowed_shelf_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in SHELF_ALLOWED_EXTENSIONS


@dashboard_bp.route('/shelf')
@login_required
def shelf():
    from models import SHELF_CATEGORIES
    items = ShelfItem.query.filter_by(creator_id=current_user.id).order_by(ShelfItem.created_at.desc()).all()
    return render_template('dashboard/shelf.html', items=items, categories=SHELF_CATEGORIES)


@dashboard_bp.route('/shelf/add', methods=['GET', 'POST'])
@login_required
def shelf_add():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category    = request.form.get('category')
        tags        = request.form.get('tags', '').strip()
        price_raw   = request.form.get('price', '0')
        currency    = request.form.get('currency', 'USD')
        is_free     = request.form.get('is_free') == 'on'

        try:
            price = 0.0 if is_free else float(price_raw)
        except ValueError:
            price = 0.0

        # Handle downloadable file
        file = request.files.get('file')
        if not file or not allowed_shelf_file(file.filename):
            flash('Please upload a valid file.', 'danger')
            return redirect(url_for('dashboard.shelf'))

        os.makedirs(SHELF_UPLOAD_FOLDER, exist_ok=True)
        filename = secure_filename(file.filename)
        # Prefix with user id to avoid collisions
        stored_name = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
        file.save(os.path.join(SHELF_UPLOAD_FOLDER, stored_name))

        # Handle cover image (optional)
        cover_name = None
        cover = request.files.get('cover_image')
        if cover and allowed_file(cover.filename):
            cover_name = f"cover_{stored_name.rsplit('.', 1)[0]}.{cover.filename.rsplit('.', 1)[1].lower()}"
            cover.save(os.path.join(UPLOAD_FOLDER, cover_name))

        item = ShelfItem(
            creator_id    = current_user.id,
            title         = title,
            description   = description,
            category      = category,
            tags          = tags,
            price         = price,
            currency      = currency,
            is_free       = is_free,
            file_path     = stored_name,
            file_name     = filename,
            file_size     = os.path.getsize(os.path.join(SHELF_UPLOAD_FOLDER, stored_name)),
            file_type     = filename.rsplit('.', 1)[1].lower(),
            cover_image   = cover_name,
            is_published  = False,
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added to your shelf!', 'success')
        return redirect(url_for('dashboard.shelf'))

    return redirect(url_for('dashboard.shelf'))


@dashboard_bp.route('/shelf/<int:item_id>/toggle', methods=['POST'])
@login_required
def shelf_toggle(item_id):
    item = ShelfItem.query.filter_by(id=item_id, creator_id=current_user.id).first_or_404()
    item.is_published = not item.is_published
    db.session.commit()
    flash(f'{"Published" if item.is_published else "Unpublished"} "{item.title}".', 'success')
    return redirect(url_for('dashboard.shelf'))


@dashboard_bp.route('/shelf/<int:item_id>/edit', methods=['POST'])
@login_required
def shelf_edit(item_id):
    item = ShelfItem.query.filter_by(id=item_id, creator_id=current_user.id).first_or_404()
    price_raw = request.form.get('price', '0')
    is_free = request.form.get('is_free') == 'on'
    try:
        price = 0.0 if is_free else float(price_raw)
    except ValueError:
        price = 0.0

    item.title = request.form.get('title', '').strip() or item.title
    item.description = request.form.get('description', '').strip() or None
    item.category = request.form.get('category') or None
    item.tags = request.form.get('tags', '').strip() or None
    item.price = price
    item.currency = request.form.get('currency', 'USD')
    item.is_free = is_free

    cover = request.files.get('cover_image')
    if cover and allowed_file(cover.filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        cover_name = f"cover_{item.id}_{int(datetime.utcnow().timestamp())}.{cover.filename.rsplit('.', 1)[1].lower()}"
        cover.save(os.path.join(UPLOAD_FOLDER, cover_name))
        item.cover_image = cover_name

    db.session.commit()
    flash(f'"{item.title}" updated.', 'success')
    return redirect(url_for('dashboard.shelf'))


@dashboard_bp.route('/shelf/<int:item_id>/delete', methods=['POST'])
@login_required
def shelf_delete(item_id):
    from models import ShelfDownload
    item = ShelfItem.query.filter_by(id=item_id, creator_id=current_user.id).first_or_404()
    # Remove any download records tied to this item first (so the FK doesn't block deletion)
    ShelfDownload.query.filter_by(item_id=item.id).delete(synchronize_session=False)
    # Remove the actual file
    file_path = os.path.join(SHELF_UPLOAD_FOLDER, item.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.title}" removed from your shelf.', 'success')
    return redirect(url_for('dashboard.shelf'))


# ── Services & Pricing ────────────────────────────────────────────────────────

@dashboard_bp.route('/services')
@login_required
def services():
    from models import Service
    items = Service.query.filter_by(
        creator_id=current_user.id
    ).order_by(Service.sort_order.asc(), Service.created_at.asc()).all()
    return render_template('dashboard/services_dashboard.html', services=items)


@dashboard_bp.route('/services/add', methods=['POST'])
@login_required
def add_service():
    from models import Service
    price_from_raw = request.form.get('price_from', '').strip()
    price_to_raw   = request.form.get('price_to', '').strip()
    try:    price_from = float(price_from_raw) if price_from_raw else None
    except: price_from = None
    try:    price_to   = float(price_to_raw)   if price_to_raw   else None
    except: price_to   = None
    svc = Service(
        creator_id  = current_user.id,
        title       = request.form.get('title', '').strip(),
        description = request.form.get('description', '').strip() or None,
        price_from  = price_from,
        price_to    = price_to,
        currency    = request.form.get('currency', 'USD'),
        unit        = request.form.get('unit', '').strip() or None,
        is_featured = bool(request.form.get('is_featured')),
    )
    db.session.add(svc)
    db.session.commit()
    flash('Service added!', 'success')
    return redirect(url_for('dashboard.services'))


@dashboard_bp.route('/services/<int:svc_id>/edit', methods=['POST'])
@login_required
def edit_service(svc_id):
    from models import Service
    svc = Service.query.filter_by(id=svc_id, creator_id=current_user.id).first_or_404()
    price_from_raw = request.form.get('price_from', '').strip()
    price_to_raw   = request.form.get('price_to', '').strip()
    try:    svc.price_from = float(price_from_raw) if price_from_raw else None
    except: svc.price_from = None
    try:    svc.price_to   = float(price_to_raw)   if price_to_raw   else None
    except: svc.price_to   = None
    svc.title       = request.form.get('title', '').strip()
    svc.description = request.form.get('description', '').strip() or None
    svc.currency    = request.form.get('currency', 'USD')
    svc.unit        = request.form.get('unit', '').strip() or None
    svc.is_featured = bool(request.form.get('is_featured'))
    db.session.commit()
    flash('Service updated!', 'success')
    return redirect(url_for('dashboard.services'))


@dashboard_bp.route('/services/<int:svc_id>/delete', methods=['POST'])
@login_required
def delete_service(svc_id):
    from models import Service
    svc = Service.query.filter_by(id=svc_id, creator_id=current_user.id).first_or_404()
    db.session.delete(svc)
    db.session.commit()
    flash('Service removed.', 'info')
    return redirect(url_for('dashboard.services'))


# ── Testimonials ──────────────────────────────────────────────────────────────

@dashboard_bp.route('/testimonials')
@login_required
def testimonials():
    from models import Testimonial
    pending  = Testimonial.query.filter_by(creator_id=current_user.id, is_approved=False).order_by(Testimonial.created_at.desc()).all()
    approved = Testimonial.query.filter_by(creator_id=current_user.id, is_approved=True).order_by(Testimonial.created_at.desc()).all()
    return render_template('dashboard/testimonials.html', pending=pending, approved=approved)


@dashboard_bp.route('/testimonials/<int:t_id>/approve', methods=['POST'])
@login_required
def approve_testimonial(t_id):
    from models import Testimonial
    t = Testimonial.query.filter_by(id=t_id, creator_id=current_user.id).first_or_404()
    t.is_approved = True
    db.session.commit()
    flash('Testimonial approved and now live on your profile.', 'success')
    return redirect(url_for('dashboard.testimonials'))


@dashboard_bp.route('/testimonials/<int:t_id>/delete', methods=['POST'])
@login_required
def delete_testimonial(t_id):
    from models import Testimonial
    t = Testimonial.query.filter_by(id=t_id, creator_id=current_user.id).first_or_404()
    db.session.delete(t)
    db.session.commit()
    flash('Testimonial removed.', 'success')
    return redirect(url_for('dashboard.testimonials'))