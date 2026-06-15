from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import send_from_directory, abort
from models import ShelfItem, ShelfDownload

import os

# ── App Init ──────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object('config.Config')

from models import db
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access your dashboard.'

from models import User, PortfolioItem, Inquiry, ContentPost, Location, Collaboration, Notification

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ── Blueprints ────────────────────────────────────────────────────────────────

from routes.auth       import auth_bp
from routes.dashboard  import dashboard_bp
from routes.public     import public_bp
from routes.api        import api_bp

app.register_blueprint(auth_bp,      url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(public_bp)
app.register_blueprint(api_bp,       url_prefix='/api')


# ── Context Processors ───────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    """Make commonly used variables available in every template."""
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, is_read=False
        ).count()
    return {
        'now': datetime.utcnow(),
        'app_name': 'Creatora',
        'unread_notifications': unread_count,
    }


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

# ── Shelf Download ────────────────────────────────────────────────────────────

@app.route('/shelf/download/<int:item_id>', methods=['GET', 'POST'])
def shelf_download(item_id):
    item = ShelfItem.query.filter_by(id=item_id, is_published=True).first_or_404()
    shelf_folder = os.path.join(app.root_path, 'static', 'shelf_files')
    os.makedirs(shelf_folder, exist_ok=True)

    # ── Paid item: show simulated checkout on GET, process on POST ────────────
    if not item.is_free and request.method == 'GET':
        return render_template('public/shelf_checkout.html', item=item)

    if not item.is_free and request.method == 'POST':
        # Simulate payment — just capture email and mark as paid
        buyer_email = request.form.get('email', '').strip()
        if not buyer_email:
            flash('Please enter your email.', 'error')
            return redirect(url_for('shelf_download', item_id=item_id))

        log = ShelfDownload(
            item_id     = item_id,
            buyer_id    = current_user.id if current_user.is_authenticated else None,
            buyer_email = buyer_email,
            amount_paid = item.price,
            currency    = item.currency,
            payment_ref = f'SIM-{item_id}-{int(datetime.utcnow().timestamp())}',
            ip_address  = request.remote_addr,
        )
        db.session.add(log)
        item.download_count += 1
        db.session.commit()
        return send_from_directory(
            shelf_folder,
            item.file_path,
            as_attachment=True,
            download_name=item.file_name
        )

    # ── Free item: log and serve immediately ──────────────────────────────────
    from datetime import timedelta
    recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
    already_downloaded = ShelfDownload.query.filter(
        ShelfDownload.item_id == item_id,
        ShelfDownload.ip_address == request.remote_addr,
        ShelfDownload.downloaded_at >= recent_cutoff,
    ).first()

    if not already_downloaded:
        log = ShelfDownload(
            item_id=item_id,
            buyer_id=current_user.id if current_user.is_authenticated else None,
            buyer_email=current_user.email if current_user.is_authenticated else None,
            amount_paid=0.0,
            ip_address=request.remote_addr,
        )
        db.session.add(log)
        item.download_count += 1
        db.session.commit()
    return send_from_directory(
        shelf_folder,
        item.file_path,
        as_attachment=True,
        download_name=item.file_name
    )
# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)