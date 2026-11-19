from flask import Blueprint, render_template
from models import Profile, ProfileDetail, Friend, Post

bp = Blueprint('social', __name__, url_prefix='/social')

@bp.get('/')
def profile():
    return render_template('social/profile.html',
        profile=Profile.query.first(),
        details=ProfileDetail.query.order_by(ProfileDetail.position, ProfileDetail.id).all(),
        friends=Friend.query.order_by(Friend.id.desc()).all(),
        posts=Post.query.order_by(Post.id.desc()).all())
