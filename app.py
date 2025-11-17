from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# --- Importaciones de Terceros ---
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func 
from werkzeug.security import generate_password_hash, check_password_hash

# --- Constantes Globales de Negocio ---
# Define el rango de horas operativas para las reservas
HORA_APERTURA = 14
HORA_CIERRE = 23

# --- Configuración de la aplicación Flask ---
app = Flask(__name__, template_folder='plantillas', static_folder='static')
app.secret_key = 'una_clave_secreta_muy_segura_aqui_12345' # ¡IMPORTANTE: Cambiar por una variable de entorno en producción!
app.permanent_session_lifetime = timedelta(minutes=30)

# --- INICIO: Configuración de la Base de Datos MySQL ---
# ¡IMPORTANTE: Usar variables de entorno en producción para estas credenciales!
USUARIO_DB = 'root'
PASS_DB = 'Lisandro22' 
HOST_DB = '127.0.0.1' 
NOMBRE_DB = 'canchas_db' 

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{USUARIO_DB}:{PASS_DB}@{HOST_DB}/{NOMBRE_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# --- FIN: Configuración de la Base de Datos MySQL ---


# --- INICIO: Definición de Modelos (Tablas de la DB) ---

class Administrador(db.Model):
    """
    Modelo de la tabla 'administradores'.
    Almacena los usuarios con permisos de administrador.
    """
    __tablename__ = 'administradores' 
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(256), nullable=False) 

    def set_password(self, contrasena):
        """Genera un hash seguro para la contraseña y lo almacena."""
        self.contrasena_hash = generate_password_hash(contrasena)

    def check_password(self, contrasena):
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return check_password_hash(self.contrasena_hash, contrasena)

class Usuario(db.Model):
    """
    Modelo de la tabla 'usuarios'.
    Almacena los usuarios regulares del sistema (clientes).
    """
    __tablename__ = 'usuarios' 
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    dni = db.Column(db.String(20), unique=True, nullable=False)
    
    # Relación: Un usuario puede tener muchas reservas
    reservas = db.relationship('Reserva', backref='usuario', lazy=True)

    def set_password(self, contrasena):
        """Genera un hash seguro para la contraseña y lo almacena."""
        self.contrasena_hash = generate_password_hash(contrasena)

    def check_password(self, contrasena):
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return check_password_hash(self.contrasena_hash, contrasena)

class Cancha(db.Model):
    """
    Modelo de la tabla 'canchas'.
    Almacena la información de cada cancha disponible.
    """
    __tablename__ = 'canchas' 
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    tipo = db.Column(db.String(50)) # Ej: "Fútbol 5", "Pádel"
    condicion = db.Column(db.String(100)) # Ej: "Techada", "Aire libre"
    monto = db.Column(db.Float, nullable=False) # Precio por hora
    
    # Relación: Una cancha puede estar en muchas reservas
    reservas = db.relationship('Reserva', backref='cancha', lazy=True)

class Reserva(db.Model):
    """
    Modelo de la tabla 'reservas'.
    Esta es la tabla central que conecta Usuarios y Canchas en una fecha/hora.
    """
    __tablename__ = 'reservas' 
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(10), nullable=False) # Formato YYYY-MM-DD
    hora_inicio = db.Column(db.String(5), nullable=False) # Formato HH:MM
    hora_fin = db.Column(db.String(5), nullable=False) # Formato HH:MM
    monto = db.Column(db.Float, nullable=False) # Monto al momento de la reserva
    estado = db.Column(db.String(20), nullable=False, default='activa') # 'activa' o 'cancelada'
    
    # Claves foráneas que establecen las relaciones
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False) 
    cancha_id = db.Column(db.Integer, db.ForeignKey('canchas.id'), nullable=False) 

class Gasto(db.Model):
    """
    ¡ESTE ES EL MODELO QUE FALTABA!
    Modelo de la tabla 'gastos'.
    Almacena todos los egresos y gastos fijos/variables del negocio.
    """
    __tablename__ = 'gastos' 
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.String(10), nullable=False) # Formato YYYY-MM-DD
    monto = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(100), nullable=False) # Ej: 'Servicios', 'Impuestos', 'Sueldos', 'Mantenimiento'
    concepto = db.Column(db.String(255), nullable=False) # Ej: 'Pago Luz Enero', 'Alquiler Mes', 'Sueldo Empleado'
    descripcion = db.Column(db.Text, nullable=True) # Opcional, para más detalles

# --- FIN: Definición de Modelos ---


# --- INICIO: Rutas de la Aplicación ---

# --- Funciones Helper ---

def verificar_admin():
    """
    Función helper de seguridad.
    Verifica si el usuario en la sesión actual es un administrador.
    """
    # Verifica que el rol 'administrador' esté en la sesión
    if 'rol' not in session or session['rol'] != 'administrador':
        flash('Acceso denegado. Por favor, inicia sesión como administrador.', 'error')
        return redirect(url_for('iniciar_sesion_administrador'))
    
    # Verifica que el ID de admin en la sesión exista en la DB
    admin = Administrador.query.get(session.get('user_id'))
    if not admin:
        flash('Sesión de administrador no válida.', 'error')
        session.clear()
        return redirect(url_for('iniciar_sesion_administrador'))
        
    return None # Si todo está OK, no retorna nada

# --- Rutas de Autenticación y Públicas ---

@app.route('/')
def inicio():
    """
    RUTA: Página de inicio (Landing page).
    Renderiza la plantilla de bienvenida 'inicio.html'.
    """
    return render_template('inicio.html')

@app.route('/crear_administrador', methods=['GET', 'POST'])
def crear_administrador():
    """
    RUTA: Registro de un nuevo Administrador.
    GET: Muestra el formulario de registro.
    POST: Procesa el formulario, valida y crea un nuevo admin en la DB.
    """
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        
        # Validación: Evitar usuarios duplicados
        admin_existente = Administrador.query.filter_by(nombre_usuario=nombre_usuario).first()
        if admin_existente:
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('crear_administrador'))

        # Creación del nuevo administrador
        nuevo_admin = Administrador(nombre_usuario=nombre_usuario)
        nuevo_admin.set_password(contrasena) # Hashea la contraseña
        
        try:
            db.session.add(nuevo_admin)
            db.session.commit()
            flash('Administrador creado exitosamente.', 'success')
            return redirect(url_for('iniciar_sesion_administrador'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear administrador: {e}', 'error')
            return redirect(url_for('crear_administrador'))
            
    return render_template('crear_administrador.html')

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    """
    RUTA: Registro de un nuevo Usuario (Cliente).
    GET: Muestra el formulario de registro.
    POST: Procesa el formulario, valida (usuario y DNI únicos) y crea un nuevo usuario.
          Inicia sesión automáticamente al usuario tras el registro.
    """
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        
        # Validación: Evitar usuarios duplicados
        user_existente = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if user_existente:
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('crear_usuario'))
            
        # Validación: Evitar DNI duplicados
        dni_existente = Usuario.query.filter_by(dni=dni).first()
        if dni_existente:
            flash('El DNI ya está registrado.', 'error')
            return redirect(url_for('crear_usuario'))

        # Creación del nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre, apellido=apellido, dni=dni, nombre_usuario=nombre_usuario
        )
        nuevo_usuario.set_password(contrasena) # Hashea la contraseña
        
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            # Autenticación automática post-registro
            session.permanent = True
            session['rol'] = 'usuario'
            session['user_id'] = nuevo_usuario.id
            session['nombre_usuario'] = nuevo_usuario.nombre_usuario
            session['nombre_completo'] = f"{nuevo_usuario.nombre} {nuevo_usuario.apellido}"
            session['dni'] = nuevo_usuario.dni
            
            return redirect(url_for('panel_usuario'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {e}', 'error')
            return redirect(url_for('crear_usuario'))
    
    return render_template('crear_usuario.html')

# --- INICIO: NUEVA RUTA PARA TORNEOS Y EVENTOS ---

@app.route('/torneos-y-eventos')
def torneos_y_eventos():
    """
    RUTA: Página pública para mostrar información de Torneos y Eventos.
    """
    # Por ahora solo renderiza la plantilla.
    # En el futuro, podrías pasarle una lista de torneos desde la base de datos.
    return render_template('torneos_y_eventos.html')

# --- FIN: NUEVA RUTA ---

@app.route('/iniciar_sesion_usuario', methods=['GET', 'POST'])
def iniciar_sesion_usuario():
    """
    RUTA: Login de Usuarios (Clientes).
    GET: Muestra el formulario de login.
    POST: Valida las credenciales (usuario y contraseña hasheada) e inicia la sesión.
    """
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        
        # Buscar al usuario en la DB
        user = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()

        # Verificar la contraseña con el hash
        if user and user.check_password(contrasena):
            session.permanent = True
            session['rol'] = 'usuario'
            session['user_id'] = user.id
            session['nombre_usuario'] = user.nombre_usuario
            session['nombre_completo'] = f"{user.nombre} {user.apellido}"
            session['dni'] = user.dni
            flash(f'¡Bienvenido, {user.nombre_usuario}!', 'success')
            return redirect(url_for('panel_usuario'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('iniciar_sesion_usuario'))
            
    return render_template('iniciar_sesion_usuario.html')

@app.route('/iniciar_sesion_administrador', methods=['GET', 'POST'])
def iniciar_sesion_administrador():
    """
    RUTA: Login de Administradores.
    GET: Muestra el formulario de login de admin.
    POST: Valida las credenciales (admin y contraseña hasheada) e inicia la sesión.
    """
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        
        # Buscar al admin en la DB
        admin = Administrador.query.filter_by(nombre_usuario=nombre_usuario).first()

        # Verificar la contraseña con el hash
        if admin and admin.check_password(contrasena):
            session.permanent = True
            session['rol'] = 'administrador'
            session['user_id'] = admin.id
            session['nombre_usuario'] = admin.nombre_usuario
            flash(f'¡Bienvenido, Administrador {admin.nombre_usuario}!', 'success')
            return redirect(url_for('panel_administrador'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('iniciar_sesion_administrador'))
            
    return render_template('iniciar_sesion_administrador.html')

@app.route('/cerrar_sesion')
def cerrar_sesion():
    """
    RUTA: Cierra la sesión (logout).
    Limpia todos los datos de la sesión y redirige al inicio.
    """
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('inicio'))

# --- Rutas del Panel de Administrador ---

@app.route('/panel_administrador')
def panel_administrador():
    """
    RUTA: Dashboard principal del Administrador.
    Protegida por 'verificar_admin()'.
    Calcula y muestra estadísticas clave (KPIs) del negocio.
    """
    # 1. Verificar permisos
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    # 2. Calcular KPIs (consultas SQL de agregación)
    total_canchas = db.session.query(func.count(Cancha.id)).scalar()
    total_usuarios = db.session.query(func.count(Usuario.id)).scalar()
    
    hoy = datetime.now().strftime('%Y-%m-%d')
    total_reservas_hoy = db.session.query(func.count(Reserva.id)).filter(
        Reserva.fecha == hoy,
        Reserva.estado == 'activa'
    ).scalar()
    
    # Calcular ingresos del mes actual
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    inicio_mes = f"{anio_actual}-{mes_actual:02d}-01"
    
    if mes_actual == 12: # Manejo del fin de año
        fin_mes = f"{anio_actual}-12-31"
    else:
        fin_mes_dt = datetime(anio_actual, mes_actual + 1, 1) - timedelta(days=1)
        fin_mes = fin_mes_dt.strftime('%Y-%m-%d')

    ingresos_mensuales = db.session.query(func.sum(Reserva.monto)).filter(
        Reserva.estado == 'activa',
        Reserva.fecha.between(inicio_mes, fin_mes)
    ).scalar() or 0.0 # 'or 0.0' para evitar que 'None' rompa la plantilla

    # 3. Renderizar plantilla con los datos
    return render_template(
        'panel_administrador.html',
        nombre_usuario=session['nombre_usuario'],
        total_canchas=total_canchas,
        total_usuarios=total_usuarios,
        total_reservas_hoy=total_reservas_hoy,
        ingresos_mensuales=round(ingresos_mensuales, 2)
    )

@app.route('/gestionar_canchas')
def gestionar_canchas():
    """
    RUTA: Ver lista de canchas (Admin).
    Protegida por 'verificar_admin()'.
    Muestra todas las canchas registradas en la DB.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    canchas = Cancha.query.all()
    return render_template('gestionar_canchas.html', canchas=canchas)

@app.route('/agregar_cancha', methods=['GET', 'POST'])
def agregar_cancha():
    """
    RUTA: Añadir una nueva cancha (Admin).
    Protegida por 'verificar_admin()'.
    GET: Muestra el formulario para agregar cancha.
    POST: Procesa el formulario, valida y crea la cancha en la DB.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        condicion = request.form['condicion']
        monto_str = request.form['monto']
        
        # Validación: Evitar canchas duplicadas por nombre
        cancha_existente = Cancha.query.filter_by(nombre=nombre).first()
        if cancha_existente:
            flash('Ya existe una cancha con ese nombre.', 'error')
            return redirect(url_for('agregar_cancha'))
            
        try:
            monto = float(monto_str)
        except ValueError:
            flash('El monto debe ser un número válido.', 'error')
            return redirect(url_for('agregar_cancha'))
            
        # Creación de la nueva cancha
        nueva_cancha = Cancha(
            nombre=nombre, tipo=tipo, condicion=condicion, monto=monto
        )
        db.session.add(nueva_cancha)
        db.session.commit()
        
        flash('Cancha agregada exitosamente.', 'success')
        return redirect(url_for('gestionar_canchas'))
    
    return render_template('agregar_cancha.html')

@app.route('/editar_cancha/<int:cancha_id>', methods=['GET', 'POST'])
def editar_cancha(cancha_id):
    """
    RUTA: Editar una cancha existente (Admin).
    Protegida por 'verificar_admin()'.
    GET: Muestra el formulario con los datos actuales de la cancha.
    POST: Procesa el formulario, valida y actualiza la cancha en la DB.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    # Busca la cancha en la DB o devuelve 404 si no existe
    cancha_a_editar = Cancha.query.get_or_404(cancha_id)
    
    if request.method == 'POST':
        nuevo_nombre = request.form['nombre']
        nuevo_tipo = request.form['tipo']
        nueva_condicion = request.form['condicion']
        nuevo_monto_str = request.form['monto']

        # Validación: Asegurar que el nuevo nombre no esté en uso por OTRA cancha
        cancha_existente = Cancha.query.filter(
            Cancha.nombre == nuevo_nombre,
            Cancha.id != cancha_id # Excluir la cancha actual de la búsqueda
        ).first()
        if cancha_existente:
            flash('Ya existe otra cancha con ese nombre.', 'error')
            return redirect(url_for('editar_cancha', cancha_id=cancha_id))
            
        try:
            nuevo_monto = float(nuevo_monto_str)
        except ValueError:
            flash('El monto debe ser un número válido.', 'error')
            return redirect(url_for('editar_cancha', cancha_id=cancha_id))

        # Actualización de datos
        cancha_a_editar.nombre = nuevo_nombre
        cancha_a_editar.tipo = nuevo_tipo
        cancha_a_editar.condicion = nueva_condicion
        cancha_a_editar.monto = nuevo_monto
        
        db.session.commit()
        flash('Cancha actualizada exitosamente.', 'success')
        return redirect(url_for('gestionar_canchas'))
    
    # Muestra el formulario con los datos precargados
    return render_template('editar_cancha.html', cancha=cancha_a_editar)

@app.route('/eliminar_cancha/<int:cancha_id>')
def eliminar_cancha(cancha_id):
    """
    RUTA: Eliminar una cancha (Admin).
    Protegida por 'verificar_admin()'.
    Valida que la cancha no tenga reservas asociadas antes de eliminar.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    cancha_a_eliminar = Cancha.query.get_or_404(cancha_id)
    
    try:
        # Validación de integridad: No eliminar canchas con historial de reservas
        reservas_asociadas = Reserva.query.filter_by(cancha_id=cancha_id).first()
        if reservas_asociadas:
            flash('Error: No se puede eliminar la cancha porque tiene reservas asociadas.', 'error')
            return redirect(url_for('gestionar_canchas'))

        # Si no hay reservas, se elimina
        db.session.delete(cancha_a_eliminar)
        db.session.commit()
        flash('Cancha eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la cancha: {e}', 'error')
        
    return redirect(url_for('gestionar_canchas'))

@app.route('/ver_turnos_administrador')
def ver_turnos_administrador():
    """
    RUTA: Ver todos los turnos activos (Admin).
    Protegida por 'verificar_admin()'.
    Muestra un listado de todas las reservas activas, agrupadas por día.
    """
    try:
        error_redirect = verificar_admin()
        if error_redirect: return error_redirect

        # Consulta que une Reservas, Usuarios y Canchas para obtener todos los datos
        reservas_db = db.session.query(Reserva, Usuario, Cancha).join(Usuario).join(Cancha).filter(
            Reserva.estado == 'activa'
        ).order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()

        # Agrupar por fecha usando un defaultdict para el template
        reservas_por_dia = defaultdict(list)
        for reserva, usuario, cancha in reservas_db:
            turno = {
                'id': reserva.id,
                'fecha': reserva.fecha,
                'hora_inicio': reserva.hora_inicio,
                'hora_fin': reserva.hora_fin,
                'cancha_nombre': cancha.nombre,
                'usuario': usuario.nombre_usuario,
                'monto_total': reserva.monto
            }
            reservas_por_dia[reserva.fecha].append(turno)

        # Ordenar los grupos de días (el más reciente primero)
        return render_template('ver_turnos_administrador.html',
                           reservas_por_dia=sorted(reservas_por_dia.items(), reverse=True))

    except Exception as e:
        flash('Error interno al mostrar los turnos', 'error')
        return render_template('ver_turnos_administrador.html', reservas_por_dia=[])

@app.route('/cancelar_turno_admin/<int:reserva_id>')
def cancelar_turno_admin(reserva_id):
    """
    RUTA: Cancelar un turno desde el panel de Admin.
    Protegida por 'verificar_admin()'.
    Cambia el estado de una reserva de 'activa' a 'cancelada'.
    """
    try:
        error_redirect = verificar_admin()
        if error_redirect: return error_redirect

        # Buscar la reserva activa
        reserva_a_cancelar = Reserva.query.filter_by(id=reserva_id, estado='activa').first()
        
        if not reserva_a_cancelar:
            flash('Turno no encontrado o ya estaba cancelado', 'error')
            return redirect(url_for('ver_turnos_administrador'))

        # Cambiar estado
        reserva_a_cancelar.estado = 'cancelada'
        db.session.commit()

        flash(f'Turno cancelado exitosamente (ID: {reserva_id})', 'success')
        return redirect(url_for('ver_turnos_administrador'))

    except Exception as e:
        db.session.rollback()
        flash('Error interno al cancelar el turno', 'error')
        return redirect(url_for('ver_turnos_administrador'))

@app.route('/gestionar_usuarios')
def gestionar_usuarios():
    """
    RUTA: Ver lista de usuarios (Admin).
    Protegida por 'verificar_admin()'.
    Muestra todos los usuarios (clientes) y administradores registrados.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    usuarios_normales = Usuario.query.all()
    administradores = Administrador.query.all()

    return render_template('gestionar_usuarios.html', usuarios=usuarios_normales, administradores=administradores)

@app.route('/ver_turnos_cancelados_administrador')
def ver_turnos_cancelados_administrador():
    """
    RUTA: Ver historial de turnos cancelados (Admin).
    Protegida por 'verificar_admin()'.
    Muestra un listado de todas las reservas con estado 'cancelada'.
    """
    try:
        error_redirect = verificar_admin()
        if error_redirect: return error_redirect

        # Consulta similar a ver_turnos, pero filtrando por 'cancelada'
        reservas_db = db.session.query(Reserva, Usuario, Cancha).join(Usuario).join(Cancha).filter(
            Reserva.estado == 'cancelada'
        ).order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()

        reservas_por_dia = defaultdict(list)
        for reserva, usuario, cancha in reservas_db:
            turno = {
                'fecha': reserva.fecha,
                'hora_inicio': reserva.hora_inicio,
                'hora_fin': reserva.hora_fin,
                'cancha_nombre': cancha.nombre,
                'usuario': usuario.nombre_usuario,
                'monto_total': reserva.monto
            }
            reservas_por_dia[reserva.fecha].append(turno)
        
        # Ordenar días (más reciente primero)
        reservas_por_dia_ordenadas = dict(sorted(reservas_por_dia.items(), reverse=True))
        
        # Ordenar horas dentro de cada día (más temprano primero)
        for fecha in reservas_por_dia_ordenadas:
            reservas_por_dia_ordenadas[fecha].sort(key=lambda x: x['hora_inicio'])

        return render_template('ver_turnos_cancelados_administrador.html',
                           reservas_por_dia=reservas_por_dia_ordenadas.items())

    except Exception as e:
        flash('Error al cargar turnos cancelados', 'error')
        return render_template('ver_turnos_cancelados_administrador.html',
                           reservas_por_dia=[])
    
@app.route('/informe_financiero_administrador')
def informe_financiero_administrador():
    """
    RUTA: Informe financiero detallado (Admin).
    ¡VERSIÓN ACTUALIZADA!
    Calcula Ingresos, Egresos y Balance Neto agrupados por período.
    """
    try:
        error_redirect = verificar_admin()
        if error_redirect: return error_redirect

        # --- 1. Contenedores de datos ---
        # Usamos defaultdict para inicializar automáticamente los períodos que no existan
        balance_diario = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0, 'balance': 0.0})
        balance_semanal = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0, 'balance': 0.0})
        balance_mensual = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0, 'balance': 0.0})
        balance_trimestral = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0, 'balance': 0.0})
        balance_anual = defaultdict(lambda: {'ingresos': 0.0, 'egresos': 0.0, 'balance': 0.0})
        
        hoy = datetime.now()
        mes_actual = hoy.month
        anio_actual = hoy.year

        # --- 2. Procesar INGRESOS (Reservas) ---
        reservas_activas = Reserva.query.filter_by(estado='activa').all()
        for r in reservas_activas:
            try:
                monto = float(r.monto)
                fecha = datetime.strptime(r.fecha, '%Y-%m-%d')
                
                # Definir períodos
                fecha_str = r.fecha
                semana = f"{fecha.year}-Sem {fecha.isocalendar()[1]:02d}"
                mes = f"{fecha.year}-{fecha.month:02d}"
                trimestre = f"{fecha.year}-T{(fecha.month-1)//3 + 1}"
                anio = str(fecha.year)

                # Sumar a ingresos
                if fecha.month == mes_actual and fecha.year == anio_actual:
                    balance_diario[fecha_str]['ingresos'] += monto
                balance_semanal[semana]['ingresos'] += monto
                balance_mensual[mes]['ingresos'] += monto
                balance_trimestral[trimestre]['ingresos'] += monto
                balance_anual[anio]['ingresos'] += monto
            except (ValueError, KeyError):
                continue
        
        # --- 3. Procesar EGRESOS (Gastos) ---
        todos_los_gastos = Gasto.query.all()
        for g in todos_los_gastos:
            try:
                monto = float(g.monto)
                fecha = datetime.strptime(g.fecha, '%Y-%m-%d')
                
                # Definir períodos
                fecha_str = g.fecha
                semana = f"{fecha.year}-Sem {fecha.isocalendar()[1]:02d}"
                mes = f"{fecha.year}-{fecha.month:02d}"
                trimestre = f"{fecha.year}-T{(fecha.month-1)//3 + 1}"
                anio = str(fecha.year)

                # Sumar a egresos
                if fecha.month == mes_actual and fecha.year == anio_actual:
                    balance_diario[fecha_str]['egresos'] += monto
                balance_semanal[semana]['egresos'] += monto
                balance_mensual[mes]['egresos'] += monto
                balance_trimestral[trimestre]['egresos'] += monto
                balance_anual[anio]['egresos'] += monto
            except (ValueError, KeyError):
                continue

        # --- 4. Calcular Balances y preparar para el template ---
        
        def calcular_y_ordenar(balance_dict):
            lista_final = []
            for periodo, datos in balance_dict.items():
                datos['balance'] = datos['ingresos'] - datos['egresos']
                lista_final.append((periodo, datos))
            # Ordenar por período (clave, ej: '2025-11') de forma descendente
            return sorted(lista_final, key=lambda item: item[0], reverse=True)

        reportes = {
            'diario': calcular_y_ordenar(balance_diario),
            'semanal': calcular_y_ordenar(balance_semanal),
            'mensual': calcular_y_ordenar(balance_mensual),
            'trimestral': calcular_y_ordenar(balance_trimestral),
            'anual': calcular_y_ordenar(balance_anual)
        }

        return render_template('informe_financiero_administrador.html', reportes=reportes)

    except Exception as e:
        flash(f'Error al generar el informe financiero: {e}', 'error')
        return render_template('informe_financiero_administrador.html', reportes={})

@app.route('/panel_reportes')
def panel_reportes():
    """
    RUTA: Panel de estadísticas y reportes de negocio (Admin).
    Protegida por 'verificar_admin()'.
    Genera múltiples reportes avanzados (Top 5, demanda, etc.).
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect

    try:
        # Reporte 1: Top 5 Usuarios con más reservas activas
        top_usuarios_reservas = db.session.query(
            Usuario.nombre_usuario, func.count(Reserva.id).label('total_reservas')
        ).join(Reserva).filter(Reserva.estado == 'activa').group_by(Usuario.id).order_by(
            func.count(Reserva.id).desc()
        ).limit(5).all()

        # Reporte 2: Top 5 Usuarios con más cancelaciones
        top_usuarios_cancelan = db.session.query(
            Usuario.nombre_usuario, func.count(Reserva.id).label('total_canceladas')
        ).join(Reserva).filter(Reserva.estado == 'cancelada').group_by(Usuario.id).order_by(
            func.count(Reserva.id).desc()
        ).limit(5).all()

        # Reporte 3: Canchas más reservadas (ranking)
        top_canchas = db.session.query(
            Cancha.nombre, func.count(Reserva.id).label('total_reservas')
        ).join(Reserva).filter(Reserva.estado == 'activa').group_by(Cancha.id).order_by(
            func.count(Reserva.id).desc()
        ).all()

        # Reporte 4: Demanda por franja horaria
        query_horarios = db.session.query(
            Reserva.hora_inicio, func.count(Reserva.id).label('total')
        ).filter(Reserva.estado == 'activa').group_by(Reserva.hora_inicio).order_by(
            func.count(Reserva.id).desc()
        ).all()
        
        # Rellenar horarios vacíos (los que tienen 0 reservas)
        contador_horarios = {h: c for h, c in query_horarios}
        for hora in range(HORA_APERTURA, HORA_CIERRE):
            hora_str = f"{hora:02d}:00"
            if hora_str not in contador_horarios:
                contador_horarios[hora_str] = 0
        
        horarios_demanda = sorted(contador_horarios.items(), key=lambda item: item[1], reverse=True)
        horarios_mas_demanda = horarios_demanda[:5]
        horarios_menos_demanda = horarios_demanda[::-1][:5]

        # Reporte 5: Días de la semana con más reservas
        mapa_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        lista_dias_semana = []
        
        # Traer solo las fechas (optimizado)
        reservas_fechas = db.session.query(Reserva.fecha).filter_by(estado='activa').all()
        
        for r in reservas_fechas:
            try:
                fecha_dt = datetime.strptime(r.fecha, '%Y-%m-%d')
                dia_idx = fecha_dt.weekday() # Lunes=0, Domingo=6
                lista_dias_semana.append(mapa_dias[dia_idx])
            except (ValueError, KeyError):
                continue
        
        # Usar Counter para contar la frecuencia de cada día
        top_dias_semana = Counter(lista_dias_semana).most_common()

        # Renderizar la plantilla con todos los reportes
        return render_template('panel_reportes.html',
                               top_usuarios_reservas=top_usuarios_reservas,
                               top_usuarios_cancelan=top_usuarios_cancelan,
                               top_canchas=top_canchas,
                               horarios_mas_demanda=horarios_mas_demanda,
                               horarios_menos_demanda=horarios_menos_demanda,
                               top_dias_semana=top_dias_semana
                               )
    except Exception as e:
        flash(f'Error al generar reportes: {e}', 'error')
        return redirect(url_for('panel_administrador'))
    
# --- INICIO: NUEVA RUTA PARA REPORTE DE GASTOS ---

@app.route('/reporte_gastos')
def reporte_gastos():
    """
    RUTA: Muestra un informe financiero y estadístico de los gastos.
    Protegida por 'verificar_admin()'.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect

    try:
        # --- 1. CÁLCULOS FINANCIEROS (Agrupación por tiempo) ---
        
        # Consultar todos los gastos para procesarlos en Python
        # (Para gastos, suele ser más fácil procesar fechas así que con SQL puro)
        todos_los_gastos = Gasto.query.all()
        
        egresos = {
            'mensuales': defaultdict(float),
            'trimestrales': defaultdict(float),
            'anuales': defaultdict(float)
        }

        for gasto in todos_los_gastos:
            try:
                monto = float(gasto.monto)
                fecha = datetime.strptime(gasto.fecha, '%Y-%m-%d')
                
                # Agrupación por mes
                mes = f"{fecha.year}-{fecha.month:02d}"
                egresos['mensuales'][mes] += monto
                
                # Agrupación por trimestre
                trimestre = f"{fecha.year}-T{(fecha.month-1)//3 + 1}"
                egresos['trimestrales'][trimestre] += monto
                
                # Agrupación por año
                egresos['anuales'][str(fecha.year)] += monto
            except (ValueError, KeyError):
                continue
        
        # Convertir a listas ordenadas para el template
        reportes_financieros = {
            'mensual': sorted(egresos['mensuales'].items(), reverse=True),
            'trimestral': sorted(egresos['trimestrales'].items(), reverse=True),
            'anual': sorted(egresos['anuales'].items(), reverse=True)
        }

        # --- 2. CÁLCULOS ESTADÍSTICOS (Rankings) ---
        
        # Reporte 1: Total gastado por Categoría
        gastos_por_categoria = db.session.query(
            Gasto.categoria, func.sum(Gasto.monto).label('total_gastado')
        ).group_by(Gasto.categoria).order_by(
            func.sum(Gasto.monto).desc()
        ).all()

        # Reporte 2: Top 10 Gastos Individuales más caros
        top_10_gastos = Gasto.query.order_by(Gasto.monto.desc()).limit(10).all()

        # Reporte 3: Meses con más gastos (basado en lo ya calculado)
        meses_mas_gastos = sorted(egresos['mensuales'].items(), key=lambda item: item[1], reverse=True)[:5]


        return render_template('reporte_gastos.html',
                               reportes_financieros=reportes_financieros,
                               gastos_por_categoria=gastos_por_categoria,
                               top_10_gastos=top_10_gastos,
                               meses_mas_gastos=meses_mas_gastos,
                               nombre_usuario=session['nombre_usuario'] # Para el sidebar
                              )

    except Exception as e:
        flash(f'Error al generar el reporte de gastos: {e}', 'error')
        return redirect(url_for('panel_administrador'))

# --- FIN: NUEVA RUTA PARA REPORTE DE GASTOS ---   

# --- INICIO: RUTAS PARA LA GESTIÓN DE GASTOS (ADMIN) ---

@app.route('/gestionar_gastos')
def gestionar_gastos():
    """
    RUTA: Ver lista de gastos (Admin).
    Protegida por 'verificar_admin()'.
    Muestra todos los gastos registrados, ordenados por fecha.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    # Consultar todos los gastos
    try:
        # Esta línea ahora funcionará porque 'Gasto' está definido arriba
        gastos = Gasto.query.order_by(Gasto.fecha.desc()).all()
    except Exception as e:
        flash(f'Error al consultar gastos: {e}', 'error')
        gastos = []
        
    now = datetime.now()
    return render_template('gestionar_gastos.html', gastos=gastos, now=now)

@app.route('/cargar_gasto', methods=['GET', 'POST'])
def cargar_gasto():
    """
    RUTA: Cargar un nuevo gasto (Admin).
    Protegida por 'verificar_admin()'.
    GET: Muestra el formulario para cargar el gasto.
    POST: Procesa el formulario y guarda el nuevo gasto en la DB.
    """
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    if request.method == 'POST':
        try:
            fecha = request.form['fecha']
            monto_str = request.form['monto']
            categoria = request.form['categoria']
            concepto = request.form['concepto']
            descripcion = request.form.get('descripcion', '')

            if not fecha or not monto_str or not categoria or not concepto:
                flash('Todos los campos obligatorios deben completarse.', 'error')
                return redirect(url_for('cargar_gasto'))
            
            monto = float(monto_str)
            if monto <= 0:
                flash('El monto debe ser un número positivo.', 'error')
                return redirect(url_for('cargar_gasto'))

            nuevo_gasto = Gasto(
                fecha=fecha,
                monto=monto,
                categoria=categoria,
                concepto=concepto,
                descripcion=descripcion
            )
            
            db.session.add(nuevo_gasto)
            db.session.commit()
            
            flash('Gasto cargado exitosamente.', 'success')
            return redirect(url_for('gestionar_gastos'))

        except ValueError:
            flash('El monto debe ser un número válido.', 'error')
            return redirect(url_for('cargar_gasto'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cargar el gasto: {e}', 'error')
            return redirect(url_for('cargar_gasto'))
    
    now = datetime.now()
    return render_template('cargar_gasto.html', now=now)

# --- FIN: RUTAS PARA LA GESTIÓN DE GASTOS ---


# --- Rutas del Panel de Usuario ---

@app.route('/panel_usuario')
def panel_usuario():
    """
    RUTA: Dashboard principal del Usuario (Cliente).
    Protegido por sesión de 'usuario'.
    Muestra los próximos turnos del usuario y un resumen de su actividad.
    """
    # 1. Verificar permisos
    if 'rol' not in session or session['rol'] != 'usuario' or 'user_id' not in session:
        flash('Acceso denegado. Por favor, inicia sesión como usuario.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))
    
    usuario_id = session['user_id']
    hoy_str = datetime.now().strftime('%Y-%m-%d')
    ahora_str = datetime.now().strftime('%H:%M')

    # 2. Obtener próximos turnos (Optimizado)
    # Filtramos en la DB por fecha >= hoy para no traer historial innecesario
    proximos_turnos_db = Reserva.query.filter(
        Reserva.usuario_id == usuario_id,
        Reserva.estado == 'activa',
        Reserva.fecha >= hoy_str 
    ).order_by(Reserva.fecha, Reserva.hora_inicio).all()
    
    proximos_turnos_con_cancha = []
    for turno in proximos_turnos_db:
        # Si el turno es hoy, verificamos que la hora no haya pasado
        if turno.fecha == hoy_str and turno.hora_inicio < ahora_str:
            continue # Omitir este turno, ya pasó

        # 'turno.cancha' funciona gracias al 'backref' de SQLAlchemy
        turno_data = {
            'id': turno.id,
            'fecha': turno.fecha,
            'hora_inicio': turno.hora_inicio,
            'hora_fin': turno.hora_fin,
            'monto': turno.monto,
            'cancha_nombre': turno.cancha.nombre,
            'cancha_tipo': turno.cancha.tipo,
            'cancha_condicion': turno.cancha.condicion
        }
        proximos_turnos_con_cancha.append(turno_data)
    
    # 3. Contar total de turnos activos para estadística
    total_turnos = Reserva.query.filter_by(usuario_id=usuario_id, estado='activa').count()

    # 4. Renderizar plantilla
    return render_template('panel_usuario.html', 
                         nombre_usuario=session['nombre_usuario'], 
                         proximos_turnos=proximos_turnos_con_cancha,
                         total_turnos=total_turnos)

@app.route('/reservar_turno', methods=['GET', 'POST'])
def reservar_turno():
    """
    RUTA: Reservar un turno (Usuario).
    Protegido por sesión de 'usuario'.
    GET: Muestra el formulario de reserva (calendario y canchas).
    POST: Procesa la reserva, validando la disponibilidad.
    """
    if 'rol' not in session or session['rol'] != 'usuario' or 'user_id' not in session:
        flash('Debes iniciar sesión como usuario para reservar un turno.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))
    
    if request.method == 'POST':
        try:
            # 1. Recoger datos del formulario
            fecha_str = request.form['fecha']
            hora_inicio_str = request.form['hora_inicio']
            cancha_id = int(request.form['cancha'])
            usuario_id = session['user_id']
            
            # 2. Obtener datos de la cancha (para el precio)
            cancha_seleccionada = Cancha.query.get(cancha_id)
            if not cancha_seleccionada:
                flash('Cancha no encontrada.', 'error')
                return redirect(url_for('reservar_turno'))

            # 3. Calcular hora de fin (asumimos 1 hora)
            hora_inicio_dt = datetime.strptime(hora_inicio_str, '%H:%M')
            hora_fin_dt = hora_inicio_dt + timedelta(hours=1)
            hora_fin_str = hora_fin_dt.strftime('%H:%M')

            # 4. Validación CRÍTICA: Verificar que el turno no esté ocupado
            reserva_existente = Reserva.query.filter_by(
                fecha=fecha_str,
                hora_inicio=hora_inicio_str,
                cancha_id=cancha_id,
                estado='activa' # Solo importa si está activa
            ).first()
            
            if reserva_existente:
                flash('Lo sentimos, el turno seleccionado ya ha sido reservado.', 'error')
                return redirect(url_for('reservar_turno'))
            
            # 5. Crear la reserva en la DB
            nueva_reserva = Reserva(
                usuario_id=usuario_id,
                cancha_id=cancha_id,
                fecha=fecha_str,
                hora_inicio=hora_inicio_str,
                hora_fin=hora_fin_str,
                monto=cancha_seleccionada.monto,
                estado='activa'
            )
            
            db.session.add(nueva_reserva)
            db.session.commit()
            
            flash('Turno reservado exitosamente.', 'success')
            return redirect(url_for('mis_turnos'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error en la reserva. Por favor, revisa los datos: {e}', 'error')
            return redirect(url_for('reservar_turno'))

    # Método GET: Cargar canchas para el formulario
    canchas = Cancha.query.all()
    return render_template('reservar_turno.html', canchas=canchas)

@app.route('/mis_turnos')
def mis_turnos():
    """
    RUTA: Ver historial de turnos (Usuario).
    Protegido por sesión de 'usuario'.
    Muestra TODOS los turnos del usuario (activos y cancelados), ordenados.
    """
    if 'rol' not in session or session['rol'] != 'usuario' or 'user_id' not in session:
        flash('Debes iniciar sesión como usuario para ver tus turnos.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))

    usuario_id = session['user_id']
    
    # Consulta que une Reservas y Canchas para el usuario logueado
    mis_reservas_db = db.session.query(Reserva, Cancha).join(Cancha).filter(
        Reserva.usuario_id == usuario_id
    ).order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()

    # Formatear los datos para el template
    mis_reservas_list = []
    for reserva, cancha in mis_reservas_db:
        mis_reservas_list.append({
            'id': reserva.id,
            'fecha': reserva.fecha,
            'hora_inicio': reserva.hora_inicio,
            'hora_fin': reserva.hora_fin,
            'monto': reserva.monto,
            'estado': reserva.estado,
            'cancha_nombre': cancha.nombre,
            'cancha_tipo': cancha.tipo,
            'cancha_condicion': cancha.condicion
        })

    return render_template('mis_turnos.html', mis_turnos=mis_reservas_list)

@app.route('/cancelar_turno/<int:reserva_id>')
def cancelar_turno(reserva_id):
    """
    RUTA: Cancelar un turno (Usuario).
    Protegido por sesión de 'usuario'.
    Verifica que el turno pertenezca al usuario y esté activo antes de cancelar.
    """
    if 'rol' not in session or session['rol'] != 'usuario' or 'user_id' not in session:
        flash('Debes iniciar sesión como usuario para cancelar un turno.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))
    
    usuario_id = session['user_id']
    
    # Buscar la reserva, asegurando que sea del usuario y esté activa
    reserva_a_cancelar = Reserva.query.filter_by(
        id=reserva_id,
        usuario_id=usuario_id,
        estado='activa' 
    ).first()
    
    if reserva_a_cancelar:
        try:
            # Lógica de cancelación: solo se cambia el estado
            reserva_a_cancelar.estado = 'cancelada'
            db.session.commit()
            flash('Turno cancelado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al cancelar el turno: {e}', 'error')
    else:
        # Si no se encuentra, es porque no existe, ya estaba cancelada o no es del usuario
        flash('No se pudo encontrar o cancelar el turno.', 'error')
        
    return redirect(url_for('mis_turnos'))

# --- Rutas de API (para JavaScript/Frontend) ---

@app.route('/api/turnos_disponibles/<fecha>')
def api_turnos_disponibles(fecha):
    """
    API ENDPOINT: Obtener horarios disponibles para una fecha específica.
    Usado por JavaScript en el formulario de reserva.
    Devuelve un JSON con la info de las canchas y los horarios ocupados/libres.
    """
    try:
        # Seguridad: Solo usuarios logueados pueden consultar la API
        if 'rol' not in session or session['rol'] != 'usuario':
            return jsonify({'error': 'No autorizado'}), 403

        # 1. Obtener todas las canchas
        canchas = Cancha.query.all()
        
        # 2. Obtener reservas activas para esa fecha
        reservas_en_fecha = Reserva.query.filter_by(
            fecha=fecha,
            estado='activa'
        ).all()

        # 3. Crear un 'set' (conjunto) de horarios ocupados para búsqueda rápida
        # Guardamos tuplas (id_cancha, hora_inicio)
        horarios_ocupados = set()
        for r in reservas_en_fecha:
            horarios_ocupados.add( (r.cancha_id, r.hora_inicio) )

        # 4. Preparar la respuesta JSON
        canchas_json = [
            {'id': c.id, 'nombre': c.nombre, 'tipo': c.tipo, 'condicion': c.condicion, 'monto': c.monto} 
            for c in canchas
        ]
        
        horarios_disponibles = {}
        for cancha in canchas:
            cancha_id = cancha.id
            horarios_disponibles[cancha_id] = []
            
            # 5. Iterar sobre el rango de horas operativas (definido en constantes)
            for hora in range(HORA_APERTURA, HORA_CIERRE):
                hora_inicio = f"{hora:02d}:00"
                hora_fin = f"{hora+1:02d}:00"
                
                # Si el turno (cancha, hora) NO está en el set de ocupados, está libre
                if (cancha_id, hora_inicio) not in horarios_ocupados:
                    horarios_disponibles[cancha_id].append({
                        'hora_inicio': hora_inicio,
                        'hora_fin': hora_fin
                    })

        # 6. Devolver la respuesta JSON
        return jsonify({
            'canchas': canchas_json,
            'horarios_disponibles': horarios_disponibles
        })

    except Exception as e:
        app.logger.error(f"Error en api_turnos_disponibles: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


# --- Final de la aplicación ---
if __name__ == '__main__':
    # El modo debug se activa para desarrollo
    # En producción, esto se gestiona con un servidor WSGI (Gunicorn, Waitress)
    app.run(debug=True)