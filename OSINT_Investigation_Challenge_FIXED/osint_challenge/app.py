import os
import secrets
from pathlib import Path
from flask import Flask, abort, g, request, session
from flask_login import current_user
from config import Config
from extensions import db, login_manager
from models import AdminUser, Profile, Setting

DEFAULT_SETTINGS = {
    'company_name': 'Super Secret Company',
    'company_tagline': 'Secure employee access gateway',
    'login_notice': 'Authorised personnel only. This is a fictional OSINT training portal.',
    'company_logo': '',
}

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)

    # Create required tables and initial public content on first launch.
    # This prevents an Internal Server Error if init-db was skipped.
    with app.app_context():
        db.create_all()
        if not Profile.query.first():
            db.session.add(Profile(name='Nuyem Limbu', username='nuyem.limbu', bio='Photographs, coffee and weekend adventures.', followers=142, friends_count=86))
        for key, value in DEFAULT_SETTINGS.items():
            if db.session.get(Setting, key) is None:
                db.session.add(Setting(key=key, value=value))
        db.session.commit()

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(AdminUser, int(user_id)) if user_id.isdigit() else None

    @app.before_request
    def csrf_guard():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            expected = session.get('_csrf_token')
            supplied = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
            if not expected or not supplied or not secrets.compare_digest(expected, supplied):
                abort(400, 'Invalid or missing form token. Refresh and try again.')

    @app.context_processor
    def globals_for_templates():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        settings = {item.key: item.value for item in Setting.query.all()}
        return {'csrf_token': session['_csrf_token'], 'settings': settings}

    from company.routes import bp as company_bp
    from social.routes import bp as social_bp
    from admin.routes import bp as admin_bp
    app.register_blueprint(company_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    @app.cli.command('init-db')
    def init_db_command():
        db.create_all()
        if not Profile.query.first():
            db.session.add(Profile(name='Nuyem Limbu', username='nuyem.limbu', bio='Photographs, coffee and weekend adventures.', followers=142, friends_count=86))
        for key, value in DEFAULT_SETTINGS.items():
            if db.session.get(Setting, key) is None:
                db.session.add(Setting(key=key, value=value))
        db.session.commit()
        print('Database ready. No security questions or answers have been prefilled.')

    @app.cli.command('create-admin')
    def create_admin_command():
        import getpass
        username = input('Admin username: ').strip()
        password = getpass.getpass('Admin password (12+ characters): ')
        if not username or len(password) < 12:
            print('A username and password of at least 12 characters are required.')
            return
        if AdminUser.query.filter_by(username=username).first():
            print('That username already exists.')
            return
        user = AdminUser(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print('Admin created.')

    return app

app = create_app()

if __name__ == '__main__':
    if os.environ.get('FLASK_DEBUG') == '1':
        app.run(debug=True)
    else:
        app.run()
