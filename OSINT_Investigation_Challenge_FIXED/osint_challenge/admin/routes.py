import uuid
from pathlib import Path
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename
from extensions import db
from models import AdminUser, Comment, Friend, Media, Post, Profile, ProfileDetail, SecurityQuestion, Setting

bp = Blueprint('admin', __name__, url_prefix='/admin')
ALLOWED = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


def to_int(value, default=0):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def upload(field):
    file = request.files.get(field)
    if not file or not file.filename:
        return None
    original = secure_filename(file.filename)
    ext = Path(original).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError('Only JPG, PNG, WebP or GIF images are permitted.')
    # Check actual file signature; do not trust extensions alone.
    header = file.stream.read(16)
    file.stream.seek(0)
    valid = (header.startswith(b'\xff\xd8\xff') if ext in ('.jpg', '.jpeg') else
             header.startswith(b'\x89PNG\r\n\x1a\n') if ext == '.png' else
             header.startswith(b'RIFF') and header[8:12] == b'WEBP' if ext == '.webp' else
             header.startswith((b'GIF87a', b'GIF89a')))
    if not valid:
        raise ValueError('The uploaded file is not a valid image of that type.')
    filename = f'{uuid.uuid4().hex}{ext}'
    file.save(Path(current_app.config['UPLOAD_FOLDER']) / filename)
    db.session.add(Media(filename=filename, original_name=original))
    return filename


@bp.get('/media/<path:filename>')
def media(filename):
    # Profile images are intentionally public; never serve other filesystem paths.
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        user = AdminUser.query.filter_by(username=request.form.get('username', '').strip()).first()
        if user and user.check_password(request.form.get('password', '')):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid admin credentials.', 'error')
    return render_template('admin/login.html')


@bp.post('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


@bp.get('/')
@login_required
def dashboard():
    return render_template('admin/dashboard.html', counts={
        'Questions': SecurityQuestion.query.count(), 'Posts': Post.query.count(),
        'Friends': Friend.query.count(), 'Comments': Comment.query.count(),
    })


@bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    keys = ['company_name', 'company_tagline', 'login_notice']
    if request.method == 'POST':
        for key in keys:
            value = request.form.get(key, '').strip()
            item = db.session.get(Setting, key) or Setting(key=key)
            item.value = value
            db.session.add(item)
        try:
            filename = upload('company_logo')
            if filename:
                item = db.session.get(Setting, 'company_logo') or Setting(key='company_logo')
                item.value = filename
                db.session.add(item)
            db.session.commit()
            flash('Company settings saved.', 'success')
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
        return redirect(url_for('admin.company'))
    return render_template('admin/company.html')


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    item = Profile.query.first()
    if request.method == 'POST':
        for key in ['name', 'username', 'bio', 'city', 'workplace', 'education']:
            setattr(item, key, request.form.get(key, '').strip())
        item.followers = to_int(request.form.get('followers'))
        item.friends_count = to_int(request.form.get('friends_count'))
        try:
            for field in ['profile_image', 'cover_image']:
                filename = upload(field)
                if filename:
                    setattr(item, field, filename)
            db.session.commit()
            flash('Profile updated.', 'success')
        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'error')
        return redirect(url_for('admin.profile'))
    return render_template('admin/profile.html', profile=item)


# Field descriptions drive a reusable create/edit form, avoiding repetitive HTML.
FIELDS = {
    'questions': [('prompt', 'Question', 'textarea'), ('answer', 'Correct answer (leave blank to keep current)', 'password'), ('position', 'Display order', 'number')],
    'friends': [('name', 'Name', 'text'), ('description', 'Description', 'text'), ('image', 'Photo', 'file')],
    'posts': [('text', 'Post text', 'textarea'), ('date', 'Date shown', 'text'), ('location', 'Location (optional)', 'text'), ('likes', 'Likes', 'number'), ('comments_count', 'Comment count', 'number'), ('image', 'Post image', 'file')],
    'details': [('label', 'About field label', 'text'), ('value', 'About field value', 'textarea'), ('position', 'Display order', 'number')],
    'comments': [('post_id', 'Post ID (see Posts page)', 'number'), ('author', 'Comment author', 'text'), ('text', 'Comment text', 'textarea')],
}
MODELS = {'questions': SecurityQuestion, 'friends': Friend, 'posts': Post, 'details': ProfileDetail, 'comments': Comment}


@bp.get('/manage/<kind>')
@login_required
def manage(kind):
    if kind not in MODELS:
        abort(404)
    items = MODELS[kind].query.order_by(MODELS[kind].id.desc()).all()
    return render_template('admin/manage.html', kind=kind, items=items, fields=FIELDS[kind])


@bp.route('/manage/<kind>/new', methods=['GET', 'POST'])
@bp.route('/manage/<kind>/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(kind, item_id=None):
    if kind not in MODELS:
        abort(404)
    model = MODELS[kind]
    item = db.session.get(model, item_id) if item_id is not None else model()
    if item is None:
        abort(404)
    if request.method == 'POST':
        try:
            for key, label, fieldtype in FIELDS[kind]:
                if fieldtype == 'file':
                    filename = upload(key)
                    if filename:
                        setattr(item, key, filename)
                elif key == 'answer':
                    answer = request.form.get('answer', '')
                    if answer.strip():
                        item.set_answer(answer)
                    elif item_id is None:
                        raise ValueError('A correct answer is required for a new question.')
                elif fieldtype == 'number':
                    setattr(item, key, to_int(request.form.get(key)))
                else:
                    setattr(item, key, request.form.get(key, '').strip())
            if kind == 'comments' and not db.session.get(Post, item.post_id):
                raise ValueError('Post ID does not exist. Create the post first.')
            db.session.add(item)
            db.session.commit()
            flash('Saved successfully.', 'success')
            return redirect(url_for('admin.manage', kind=kind))
        except (ValueError, TypeError) as e:
            db.session.rollback()
            flash(str(e), 'error')
    return render_template('admin/edit.html', kind=kind, item=item, fields=FIELDS[kind], is_new=item_id is None)


@bp.post('/manage/<kind>/<int:item_id>/delete')
@login_required
def delete(kind, item_id):
    if kind not in MODELS:
        abort(404)
    item = db.get_or_404(MODELS[kind], item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', 'success')
    return redirect(url_for('admin.manage', kind=kind))


@bp.get('/media-library')
@login_required
def media_library():
    return render_template('admin/media.html', items=Media.query.order_by(Media.id.desc()).all())
