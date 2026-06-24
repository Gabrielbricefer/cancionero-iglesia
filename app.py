import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Song, Playlist, PlaylistSong
import secrets
import re

app = Flask(__name__)

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-por-defecto-cambiar-en-produccion')
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'cancionero.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    
    # ========== CREAR SUPERUSUARIO POR DEFECTO ==========
    # Comentado para evitar creación automática del usuario 'admin'
    # admin = User.query.filter_by(username='admin').first()
    # if not admin:
    #     admin = User(
    #         username='admin',
    #         password_hash=generate_password_hash('admin123'),
    #         is_admin=True,
    #         is_blocked=False
    #     )
    #     db.session.add(admin)
    #     db.session.commit()
    #     print("Superusuario 'admin' creado con contraseña 'admin123'")

# ========== DECORADOR PARA VERIFICAR ADMIN ==========
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ========== RUTAS PÚBLICAS ==========
@app.route('/')
def index():
    query = Song.query
    category_order = request.args.get('order')
    category_time = request.args.get('time')
    search = request.args.get('search')
    
    if category_order and category_order != '':
        query = query.filter_by(category_order=category_order)
    if category_time and category_time != '':
        query = query.filter_by(category_time=category_time)
    if search:
        query = query.filter(Song.title.contains(search) | Song.lyrics.contains(search))
    
    songs = query.order_by(Song.title).all()
    
    orden_misa_opciones = ['entrada', 'piedad', 'gloria', 'aclamación del evangelio', 
                          'ofertorio', 'santo', 'cordero', 'comunión', 'salida', 'extras']
    tiempo_liturgico_opciones = ['adviento', 'navidad', 'tiempo ordinario', 
                                'cuaresma', 'triduo pascual', 'pascua', 'extra']
    
    return render_template('index.html', 
                         songs=songs, 
                         orden_misa_opciones=orden_misa_opciones,
                         tiempo_liturgico_opciones=tiempo_liturgico_opciones,
                         selected_order=category_order,
                         selected_time=category_time,
                         search=search)

# ========== AUTENTICACIÓN ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Verificar si el usuario está bloqueado
            if user.is_blocked:
                flash('Esta cuenta ha sido bloqueada. Contacta al administrador.', 'danger')
                return render_template('login.html')
            
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            flash('Las contraseñas no coinciden', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'danger')
        else:
            hashed = generate_password_hash(password)
            user = User(username=username, password_hash=hashed)
            db.session.add(user)
            db.session.commit()
            flash('Registro exitoso, ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))

# ========== GESTIÓN DE CANCIONES ==========
@app.route('/create_song', methods=['GET', 'POST'])
@login_required
def create_song():
    # Verificar si el usuario está bloqueado
    if current_user.is_blocked:
        flash('Tu cuenta está bloqueada. No puedes crear canciones.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        lyrics = request.form['lyrics']
        category_order = request.form['category_order']
        category_time = request.form['category_time']
        
        if not title or not lyrics:
            flash('Título y letra son obligatorios', 'danger')
        else:
            song = Song(
                title=title,
                lyrics=lyrics,
                category_order=category_order,
                category_time=category_time,
                user_id=current_user.id
            )
            db.session.add(song)
            db.session.commit()
            flash('Canción creada exitosamente', 'success')
            return redirect(url_for('my_songs'))
    
    orden_misa_opciones = ['entrada', 'piedad', 'gloria', 'aclamación del evangelio', 
                          'ofertorio', 'santo', 'cordero', 'comunión', 'salida', 'extras']
    tiempo_liturgico_opciones = ['adviento', 'navidad', 'tiempo ordinario', 
                                'cuaresma', 'triduo pascual', 'pascua', 'extra']
    
    return render_template('create_song.html',
                         orden_misa_opciones=orden_misa_opciones,
                         tiempo_liturgico_opciones=tiempo_liturgico_opciones)

@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@login_required
def edit_song(song_id):
    song = Song.query.get_or_404(song_id)
    
    # Permitir edición si es el autor O si es administrador
    if song.user_id != current_user.id and not current_user.is_admin:
        flash('No tienes permiso para editar esta canción', 'danger')
        return redirect(url_for('index'))
    
    # Verificar si el usuario está bloqueado (excepto admin)
    if current_user.is_blocked and not current_user.is_admin:
        flash('Tu cuenta está bloqueada.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        song.title = request.form['title']
        song.lyrics = request.form['lyrics']
        song.category_order = request.form['category_order']
        song.category_time = request.form['category_time']
        db.session.commit()
        flash('Canción actualizada', 'success')
        return redirect(url_for('my_songs') if song.user_id == current_user.id else url_for('admin_songs'))
    
    orden_misa_opciones = ['entrada', 'piedad', 'gloria', 'aclamación del evangelio', 
                          'ofertorio', 'santo', 'cordero', 'comunión', 'salida', 'extras']
    tiempo_liturgico_opciones = ['adviento', 'navidad', 'tiempo ordinario', 
                                'cuaresma', 'triduo pascual', 'pascua', 'extra']
    
    return render_template('edit_song.html', song=song,
                         orden_misa_opciones=orden_misa_opciones,
                         tiempo_liturgico_opciones=tiempo_liturgico_opciones)

@app.route('/delete_song/<int:song_id>')
@login_required
def delete_song(song_id):
    song = Song.query.get_or_404(song_id)
    
    # Permitir eliminación si es el autor O si es administrador
    if song.user_id != current_user.id and not current_user.is_admin:
        flash('No autorizado', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(song)
    db.session.commit()
    flash('Canción eliminada', 'success')
    return redirect(url_for('my_songs') if song.user_id == current_user.id else url_for('admin_songs'))

@app.route('/my_songs')
@login_required
def my_songs():
    if current_user.is_blocked:
        flash('Tu cuenta está bloqueada.', 'danger')
        return redirect(url_for('index'))
    
    songs = Song.query.filter_by(user_id=current_user.id).order_by(Song.title).all()
    return render_template('my_songs.html', songs=songs)

# ========== ADMINISTRACIÓN ==========
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_songs = Song.query.count()
    blocked_users = User.query.filter_by(is_blocked=True).count()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         total_songs=total_songs,
                         blocked_users=blocked_users)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/toggle_block/<int:user_id>')
@login_required
@admin_required
def admin_toggle_block(user_id):
    user = User.query.get_or_404(user_id)
    
    # No permitir bloquear al propio admin
    if user.id == current_user.id:
        flash('No puedes bloquearte a ti mismo', 'danger')
        return redirect(url_for('admin_users'))
    
    user.is_blocked = not user.is_blocked
    db.session.commit()
    status = 'bloqueado' if user.is_blocked else 'desbloqueado'
    flash(f'Usuario {user.username} {status} exitosamente', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/songs')
@login_required
@admin_required
def admin_songs():
    songs = Song.query.order_by(Song.created_at.desc()).all()
    return render_template('admin_songs.html', songs=songs)

# ========== PLANIFICAR MISA ==========
@app.route('/plan_misa')
@login_required
def plan_misa():
    if current_user.is_blocked:
        flash('Tu cuenta está bloqueada.', 'danger')
        return redirect(url_for('index'))
    
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    all_songs = Song.query.order_by(Song.title).all()
    return render_template('plan_misa.html', playlists=playlists, all_songs=all_songs)

@app.route('/create_playlist', methods=['POST'])
@login_required
def create_playlist():
    if current_user.is_blocked:
        flash('Tu cuenta está bloqueada.', 'danger')
        return redirect(url_for('index'))
    
    name = request.form['name']
    if not name:
        flash('Nombre de lista requerido', 'danger')
        return redirect(url_for('plan_misa'))
    
    token = secrets.token_urlsafe(16)
    playlist = Playlist(name=name, user_id=current_user.id, share_token=token)
    db.session.add(playlist)
    db.session.commit()
    flash('Lista creada', 'success')
    return redirect(url_for('plan_misa'))

@app.route('/add_song_to_playlist', methods=['POST'])
@login_required
def add_song_to_playlist():
    playlist_id = request.form['playlist_id']
    song_id = request.form['song_id']
    
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        flash('No autorizado', 'danger')
        return redirect(url_for('plan_misa'))
    
    existing = PlaylistSong.query.filter_by(playlist_id=playlist_id, song_id=song_id).first()
    if existing:
        flash('La canción ya está en la lista', 'warning')
        return redirect(url_for('plan_misa'))
    
    max_order = db.session.query(db.func.max(PlaylistSong.order_position)).filter_by(playlist_id=playlist_id).scalar() or 0
    ps = PlaylistSong(playlist_id=playlist_id, song_id=song_id, order_position=max_order + 1)
    db.session.add(ps)
    db.session.commit()
    flash('Canción agregada', 'success')
    return redirect(url_for('plan_misa'))

@app.route('/remove_song_from_playlist/<int:playlist_song_id>')
@login_required
def remove_song_from_playlist(playlist_song_id):
    ps = PlaylistSong.query.get_or_404(playlist_song_id)
    playlist = Playlist.query.get(ps.playlist_id)
    if playlist.user_id != current_user.id:
        flash('No autorizado', 'danger')
        return redirect(url_for('plan_misa'))
    
    db.session.delete(ps)
    db.session.commit()
    flash('Canción removida', 'success')
    return redirect(url_for('plan_misa'))

@app.route('/playlist/<token>')
def shared_playlist(token):
    playlist = Playlist.query.filter_by(share_token=token).first_or_404()
    playlist_songs = PlaylistSong.query.filter_by(playlist_id=playlist.id).order_by(PlaylistSong.order_position).all()
    return render_template('shared_playlist.html', playlist=playlist, playlist_songs=playlist_songs)

@app.route('/delete_playlist/<int:playlist_id>')
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        flash('No autorizado', 'danger')
        return redirect(url_for('plan_misa'))
    db.session.delete(playlist)
    db.session.commit()
    flash('Lista eliminada', 'success')
    return redirect(url_for('plan_misa'))

if __name__ == '__main__':
    app.run(debug=True)