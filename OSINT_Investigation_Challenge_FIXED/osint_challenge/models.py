from flask_login import UserMixin
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class AdminUser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Setting(db.Model):
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False, default='')

class SecurityQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.String(500), nullable=False)
    answer_hash = db.Column(db.String(255), nullable=False)
    position = db.Column(db.Integer, default=0)

    @staticmethod
    def normalize(answer):
        # Case-insensitive; ignore extra spaces without accepting misspellings.
        return ' '.join((answer or '').split()).casefold()

    def set_answer(self, answer):
        self.answer_hash = generate_password_hash(self.normalize(answer))

    def matches(self, answer):
        return check_password_hash(self.answer_hash, self.normalize(answer))

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), default='Nuyem Limbu')
    username = db.Column(db.String(80), default='nuyem.limbu')
    bio = db.Column(db.Text, default='Collecting little moments, one day at a time.')
    city = db.Column(db.String(150), default='')
    workplace = db.Column(db.String(150), default='')
    education = db.Column(db.String(150), default='')
    profile_image = db.Column(db.String(255), default='')
    cover_image = db.Column(db.String(255), default='')
    followers = db.Column(db.Integer, default=0)
    friends_count = db.Column(db.Integer, default=0)

class ProfileDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, default=0)

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(250), default='')
    image = db.Column(db.String(255), default='')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), default='')
    date = db.Column(db.String(60), default='')
    location = db.Column(db.String(150), default='')
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    text = db.Column(db.Text, nullable=False)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    original_name = db.Column(db.String(255), default='')
