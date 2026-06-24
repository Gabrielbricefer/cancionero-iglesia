from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    security_question = db.Column(db.String(200), nullable=True)  # Pregunta de seguridad
    security_answer = db.Column(db.String(200), nullable=True)    # Respuesta (hasheada)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    songs = db.relationship('Song', backref='author', lazy=True, cascade='all, delete-orphan')
    playlists = db.relationship('Playlist', backref='owner', lazy=True, cascade='all, delete-orphan')

class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    category_order = db.Column(db.String(50), nullable=False)
    category_time = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    share_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    songs = db.relationship('PlaylistSong', backref='playlist', lazy=True, cascade='all, delete-orphan')

class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    order_position = db.Column(db.Integer, nullable=False)
    
    song = db.relationship('Song')