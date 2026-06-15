from flask import Blueprint, jsonify, request
from flask import url_for
from models import Location, Collaboration, User
from flask_login import login_required, current_user

api_bp = Blueprint('api', __name__)


@api_bp.route('/locations')
def locations():
    """Return all SceneScout locations as GeoJSON for the map."""
    locs = Location.query.all()
    features = [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [l.lng, l.lat]},
            'properties': {
                'id': l.id, 'name': l.name, 'category': l.category,
                'vibe': l.vibe, 'best_time': l.best_time,
                'crowd_level': l.crowd_level, 'image': l.image,
                'creator_username': l.creator.username if l.creator else None,
                'creator_name': (l.creator.display_name or l.creator.username) if l.creator else None,
                'creator_profile_url': url_for('public.profile', username=l.creator.username) if l.creator else None,
            }
        }
        for l in locs if l.lat and l.lng
    ]
    return jsonify({'type': 'FeatureCollection', 'features': features})
