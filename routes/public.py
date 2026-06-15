from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from models import User, PortfolioItem, Inquiry, Location, Collaboration, Notification, ShelfItem, db
from config import Config
from flask_login import login_required, current_user

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    featured = User.query.filter_by(is_public=True).limit(6).all()
    return render_template('public/index.html', featured=featured)


@public_bp.route('/creators')
def directory():
    role     = request.args.get('role', '')
    page     = request.args.get('page', 1, type=int)
    query    = User.query.filter_by(is_public=True)
    if role:
        query = query.filter_by(role=role)
    creators = query.paginate(page=page, per_page=Config.CREATORS_PER_PAGE)
    return render_template('public/directory.html', creators=creators, active_role=role)


@public_bp.route('/c/<username>')
def profile(username):
    from models import Testimonial, Service
    creator = User.query.filter_by(username=username).first_or_404()

    is_owner = current_user.is_authenticated and current_user.id == creator.id
    if not creator.is_public and not is_owner:
        abort(404)

    portfolio    = PortfolioItem.query.filter_by(creator_id=creator.id).all()
    testimonials = Testimonial.query.filter_by(creator_id=creator.id, is_approved=True).order_by(Testimonial.created_at.desc()).all()
    services     = Service.query.filter_by(creator_id=creator.id).order_by(Service.is_featured.desc(), Service.sort_order.asc()).all()

    if not is_owner:
        creator.profile_views = (creator.profile_views or 0) + 1
    db.session.commit()
    return render_template('public/profile.html', creator=creator, portfolio=portfolio, testimonials=testimonials, services=services)


@public_bp.route('/c/<username>/inquire', methods=['POST'])
def send_inquiry(username):
    creator = User.query.filter_by(username=username).first_or_404()
    inquiry = Inquiry(
        creator_id=creator.id,
        name=request.form['name'],
        email=request.form['email'],
        message=request.form['message'],
    )
    db.session.add(inquiry)

    # ── Fire notification ──
    notif = Notification(
        user_id=creator.id,
        type='inquiry',
        title='New inquiry received',
        message=f"{request.form['name']} sent you an inquiry.",
        link='/dashboard/crm',
    )
    db.session.add(notif)
    db.session.commit()

    flash('Your inquiry has been sent!', 'success')
    return redirect(url_for('public.profile', username=username))


@public_bp.route('/scenescout')
def scenescout():
    cat = request.args.get('cat', '')
    query = Location.query
    if cat:
        query = query.filter_by(category=cat)
    locations = query.all()
    return render_template('public/scenescout.html', locations=locations, active_cat=cat)


@public_bp.route('/collabs')
def collabs():
    collabs = Collaboration.query.filter_by(is_open=True).order_by(
        Collaboration.created_at.desc()
    ).all()
    return render_template('public/collabs.html', collabs=collabs)


@public_bp.route('/collabs/post', methods=['POST'])
@login_required
def post_collab():
    from datetime import datetime
    deadline_str = request.form.get('deadline')
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d') if deadline_str else None

    collab = Collaboration(
        creator_id=current_user.id,
        title=request.form['title'],
        description=request.form.get('description'),
        role_needed=request.form.get('role_needed') or None,
        location=request.form.get('location') or None,
        deadline=deadline,
        is_open=True,
    )
    db.session.add(collab)

    # ── Fire notification ──
    notif = Notification(
        user_id=current_user.id,
        type='collab',
        title='Collab post is live!',
        message=f'"{request.form["title"]}" is now visible on the public collabs board.',
        link='/dashboard/collabs/my',
    )
    db.session.add(notif)
    db.session.commit()

    flash('Your collaboration call is live!', 'success')
    return redirect(url_for('public.collabs'))


@public_bp.route('/collabs/<int:collab_id>/interest', methods=['POST'])
def collab_interest(collab_id):
    collab = Collaboration.query.filter_by(id=collab_id, is_open=True).first_or_404()
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()

    if not name or not email or not message:
        flash('Please add your name, email, and a message.', 'danger')
        return redirect(url_for('public.collabs'))

    inquiry = Inquiry(
        creator_id=collab.creator_id,
        name=name,
        email=email,
        message=f'Collab interest for "{collab.title}":\n\n{message}',
    )
    db.session.add(inquiry)

    notif = Notification(
        user_id=collab.creator_id,
        type='collab_interest',
        title='New collab interest',
        message=f'{name} responded to "{collab.title}".',
        link='/dashboard/crm',
    )
    db.session.add(notif)
    db.session.commit()

    flash('Your message has been sent to the creator.', 'success')
    return redirect(url_for('public.collabs'))

@public_bp.route('/shelf/<username>')
def creator_shelf(username):
    creator = User.query.filter_by(username=username).first_or_404()

    is_owner = current_user.is_authenticated and current_user.id == creator.id
    if not creator.is_public and not is_owner:
        abort(404)

    items = ShelfItem.query.filter_by(
        creator_id=creator.id,
        is_published=True
    ).order_by(ShelfItem.created_at.desc()).all()
    return render_template('public/creator_shelf.html', creator=creator, items=items)

@public_bp.route('/c/<username>/testimonial', methods=['POST'])
def submit_testimonial(username):
    from models import Testimonial, Notification
    creator = User.query.filter_by(username=username).first_or_404()

    author_name  = request.form.get('author_name', '').strip()
    author_title = request.form.get('author_title', '').strip()
    author_email = request.form.get('author_email', '').strip()
    body         = request.form.get('body', '').strip()
    try:
        rating = int(request.form.get('rating', 5))
    except ValueError:
        rating = 5

    if not author_name or not body:
        flash('Please fill in your name and testimonial.', 'danger')
        return redirect(url_for('public.profile', username=username) + '#leave-review')

    rating = max(1, min(5, rating))

    t = Testimonial(
        creator_id   = creator.id,
        author_name  = author_name,
        author_title = author_title or None,
        author_email = author_email or None,
        body         = body,
        rating       = rating,
        is_approved  = False,
    )
    db.session.add(t)

    notif = Notification(
        user_id = creator.id,
        type    = 'testimonial',
        title   = 'New testimonial submitted',
        message = f'New testimonial from {author_name} — pending your approval.',
        link    = '/dashboard/testimonials',
    )
    db.session.add(notif)
    db.session.commit()

    flash('Thanks! Your testimonial has been submitted and will appear after the creator approves it.', 'success')
    return redirect(url_for('public.profile', username=username))