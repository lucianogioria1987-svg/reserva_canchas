from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

# --- Configuración de la aplicación Flask ---
app = Flask(__name__, template_folder='plantillas', static_folder='static')
app.secret_key = 'una_clave_secreta_muy_segura_aqui_12345'
app.permanent_session_lifetime = timedelta(minutes=30)

# Rutas a los archivos JSON (dentro de la carpeta 'datos')
CARPETA_DATOS = os.path.join(os.path.dirname(__file__), 'datos')
USUARIOS_ADMIN_FILE = os.path.join(CARPETA_DATOS, 'administradores.json')
USUARIOS_NORMAL_FILE = os.path.join(CARPETA_DATOS, 'usuarios.json')
RESERVAS_FILE = os.path.join(CARPETA_DATOS, 'reservas.json')
CANCHAS_FILE = os.path.join(CARPETA_DATOS, 'canchas.json')
RESERVAS_CANCELADAS_FILE = os.path.join(CARPETA_DATOS, 'reservas_canceladas.json')

# --- Funciones Auxiliares para JSON ---
def cargar_datos_json(filepath):
    """Carga datos desde un archivo JSON. Si no existe o está vacío/corrupto, retorna una lista vacía."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except (json.JSONDecodeError, Exception) as e:
        return []

def guardar_datos_json(filepath, data):
    """Guarda datos en un archivo JSON."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        pass

# Función para verificar si es administrador
def verificar_admin():
    if 'rol' not in session or session['rol'] != 'administrador':
        flash('Acceso denegado. Por favor, inicia sesión como administrador.', 'error')
        return redirect(url_for('iniciar_sesion_administrador'))
    return None

# --- Rutas de la Aplicación ---

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/crear_administrador', methods=['GET', 'POST'])
def crear_administrador():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        administradores = cargar_datos_json(USUARIOS_ADMIN_FILE)

        if any(admin['nombre_usuario'] == nombre_usuario for admin in administradores):
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('crear_administrador'))

        administradores.append({'nombre_usuario': nombre_usuario, 'contrasena': contrasena})
        guardar_datos_json(USUARIOS_ADMIN_FILE, administradores)
        flash('Administrador creado exitosamente. ¡Ahora inicia sesión!', 'success')
        return redirect(url_for('iniciar_sesion_administrador'))
    return render_template('crear_administrador.html')

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        usuarios = cargar_datos_json(USUARIOS_NORMAL_FILE)

        # Verificar si el nombre de usuario ya existe
        if any(user['nombre_usuario'] == nombre_usuario for user in usuarios):
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('crear_usuario'))
            
        # Verificar si el DNI ya existe
        if any(user.get('dni') == dni for user in usuarios):
            flash('El DNI ya está registrado.', 'error')
            return redirect(url_for('crear_usuario'))

        # Crear nuevo usuario con todos los campos
        nuevo_usuario = {
            'nombre': nombre,
            'apellido': apellido,
            'dni': dni,
            'nombre_usuario': nombre_usuario,
            'contrasena': contrasena
        }

        usuarios.append(nuevo_usuario)
        guardar_datos_json(USUARIOS_NORMAL_FILE, usuarios)
        
        # Iniciar sesión automáticamente después del registro
        session.permanent = True
        session['rol'] = 'usuario'
        session['nombre_usuario'] = nombre_usuario
        session['nombre_completo'] = f"{nombre} {apellido}"
        session['dni'] = dni
        
        # Redirigir al panel de usuario
        return redirect(url_for('panel_usuario'))
    
    return render_template('crear_usuario.html')

@app.route('/iniciar_sesion_usuario', methods=['GET', 'POST'])
def iniciar_sesion_usuario():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        usuarios = cargar_datos_json(USUARIOS_NORMAL_FILE)

        user_found = False
        for user in usuarios:
            if user['nombre_usuario'] == nombre_usuario and user['contrasena'] == contrasena:
                session.permanent = True
                session['rol'] = 'usuario'
                session['nombre_usuario'] = nombre_usuario
                session['nombre_completo'] = f"{user.get('nombre', '')} {user.get('apellido', '')}"
                session['dni'] = user.get('dni', '')
                flash(f'¡Bienvenido, {nombre_usuario}!', 'success')
                user_found = True
                break

        if user_found:
            return redirect(url_for('panel_usuario'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('iniciar_sesion_usuario'))
    return render_template('iniciar_sesion_usuario.html')
@app.route('/iniciar_sesion_administrador', methods=['GET', 'POST'])
def iniciar_sesion_administrador():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        administradores = cargar_datos_json(USUARIOS_ADMIN_FILE)

        admin_found = False
        for admin in administradores:
            if admin['nombre_usuario'] == nombre_usuario and admin['contrasena'] == contrasena:
                session.permanent = True
                session['rol'] = 'administrador'
                session['nombre_usuario'] = nombre_usuario
                flash(f'¡Bienvenido, Administrador {nombre_usuario}!', 'success')
                admin_found = True
                break

        if admin_found:
            return redirect(url_for('panel_administrador'))
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'error')
            return redirect(url_for('iniciar_sesion_administrador'))
    return render_template('iniciar_sesion_administrador.html')

@app.route('/panel_administrador')
def panel_administrador():
    error_redirect = verificar_admin()
    if error_redirect: 
        return error_redirect
    
    # Cargar datos necesarios
    canchas = cargar_datos_json(CANCHAS_FILE)
    usuarios = cargar_datos_json(USUARIOS_NORMAL_FILE)
    reservas = cargar_datos_json(RESERVAS_FILE)
    
    # 1. Total de canchas
    total_canchas = len(canchas)
    
    # 2. Total de usuarios
    total_usuarios = len(usuarios)
    
    # 3. Reservas hoy (fecha actual)
    hoy = datetime.now().strftime('%Y-%m-%d')
    reservas_hoy = [r for r in reservas if r['fecha'] == hoy]
    
    # Contar reservas únicas (agrupadas por clave_agrupacion)
    reservas_unicas = set()
    for r in reservas_hoy:
        reservas_unicas.add(r['clave_agrupacion'])
    total_reservas_hoy = len(reservas_unicas)
    
    # 4. Ingresos mensuales (mes calendario actual)
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    ingresos_mensuales = 0.0
    
    for r in reservas:
        try:
            fecha_reserva = datetime.strptime(r['fecha'], '%Y-%m-%d')
            if fecha_reserva.month == mes_actual and fecha_reserva.year == anio_actual:
                ingresos_mensuales += float(r['cancha_monto'])
        except:
            continue

    return render_template(
        'panel_administrador.html',
        nombre_usuario=session['nombre_usuario'],
        total_canchas=total_canchas,
        total_usuarios=total_usuarios,
        total_reservas_hoy=total_reservas_hoy,
        ingresos_mensuales=round(ingresos_mensuales, 2)
    )

@app.route('/panel_usuario')
def panel_usuario():
    if 'rol' not in session or session['rol'] != 'usuario':
        flash('Acceso denegado. Por favor, inicia sesión como usuario.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))
    
    usuario = session['nombre_usuario']
    
    # Obtener los turnos del usuario
    reservas = cargar_datos_json(RESERVAS_FILE)
    
    # Agrupar las reservas de 30 minutos en turnos de 1 hora para visualización
    mis_reservas_agrupadas = defaultdict(dict)
    for r in sorted(reservas, key=lambda x: (x['fecha'], x['hora_inicio'])):
        if r['usuario'] == usuario:
            clave = r['clave_agrupacion']
            if clave not in mis_reservas_agrupadas:
                mis_reservas_agrupadas[clave] = {
                    'fecha': r['fecha'],
                    'cancha_id': r['cancha_id'],
                    'cancha_nombre': r['cancha_nombre'],
                    'cancha_tipo': r.get('cancha_tipo', 'N/A'),
                    'cancha_condicion': r.get('cancha_condicion', 'N/A'),
                    'monto': 0,
                    'bloques': [],
                    'id': r['id'],
                    'clave_agrupacion': clave,
                    'hora_inicio': r['hora_inicio'],
                    'hora_fin': ''
                }
            mis_reservas_agrupadas[clave]['bloques'].append(r)
            mis_reservas_agrupadas[clave]['monto'] += r['cancha_monto']
            mis_reservas_agrupadas[clave]['hora_fin'] = r['hora_fin']
    
    todos_los_turnos = sorted(list(mis_reservas_agrupadas.values()), 
                       key=lambda x: (x['fecha'], x['hora_inicio']))
    
    # Filtrar solo los próximos turnos (a partir de hoy)
    hoy = datetime.now().strftime('%Y-%m-%d')
    ahora = datetime.now().strftime('%H:%M')
    
    proximos_turnos = []
    for turno in todos_los_turnos:
        # Si la fecha del turno es hoy, verificar la hora
        if turno['fecha'] == hoy:
            if turno['hora_inicio'] >= ahora:
                proximos_turnos.append(turno)
        # Si la fecha del turno es futura
        elif turno['fecha'] > hoy:
            proximos_turnos.append(turno)
    
    # Ordenar los próximos turnos por fecha y hora
    proximos_turnos = sorted(proximos_turnos, key=lambda x: (x['fecha'], x['hora_inicio']))

    return render_template('panel_usuario.html', 
                         nombre_usuario=usuario, 
                         proximos_turnos=proximos_turnos,
                         total_turnos=len(todos_los_turnos))

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('nombre_usuario', None)
    session.pop('rol', None)
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('inicio'))

# --- RUTAS PARA LAS FUNCIONES DE USUARIO ---

@app.route('/reservar_turno', methods=['GET', 'POST'])
def reservar_turno():
    if 'rol' not in session or session['rol'] != 'usuario':
        flash('Debes iniciar sesión como usuario para reservar un turno.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))
    
    if request.method == 'POST':
        try:
            fecha_str = request.form['fecha']
            hora_inicio_str = request.form['hora_inicio']
            cancha_id = int(request.form['cancha'])
            usuario = session['nombre_usuario']
            
            canchas = cargar_datos_json(CANCHAS_FILE)
            reservas = cargar_datos_json(RESERVAS_FILE)
            cancha_seleccionada = next((c for c in canchas if c['id'] == cancha_id), None)

            if not cancha_seleccionada:
                flash('Cancha no encontrada.', 'error')
                return redirect(url_for('reservar_turno'))

            # Convertir fechas y horas a objetos datetime
            fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
            hora_inicio_dt = datetime.strptime(hora_inicio_str, '%H:%M')
            
            # Crear los dos bloques de 30 minutos
            hora_bloque1_dt = hora_inicio_dt
            hora_bloque2_dt = hora_inicio_dt + timedelta(minutes=30)
            
            fecha_bloque1 = fecha_str
            fecha_bloque2 = fecha_str
            
            # Convertir a formato de cadena para guardar en JSON
            hora_bloque1_str = hora_bloque1_dt.strftime('%H:%M')
            hora_bloque2_str = hora_bloque2_dt.strftime('%H:%M')
            hora_fin_str = (hora_inicio_dt + timedelta(hours=1)).strftime('%H:%M')

            # Validar que los turnos no estén ocupados
            reserva_existente1 = any(r['fecha'] == fecha_bloque1 and r['hora_inicio'] == hora_bloque1_str and r['cancha_id'] == cancha_id for r in reservas)
            reserva_existente2 = any(r['fecha'] == fecha_bloque2 and r['hora_inicio'] == hora_bloque2_str and r['cancha_id'] == cancha_id for r in reservas)
            
            if reserva_existente1 or reserva_existente2:
                flash('Lo sentimos, al menos uno de los turnos seleccionados ya ha sido reservado.', 'error')
                return redirect(url_for('reservar_turno'))
            
            max_id = max([r['id'] for r in reservas]) if reservas else 0
            
            # Generar una clave única para agrupar los dos bloques del turno de 1 hora
            clave_agrupacion = f"{usuario}-{fecha_str}-{hora_inicio_str}-{cancha_id}"

            # Guardar ambos turnos de 30 minutos con la clave de agrupación
            nueva_reserva1 = {
                'id': max_id + 1,
                'clave_agrupacion': clave_agrupacion,
                'usuario': usuario,
                'fecha': fecha_bloque1,
                'hora_inicio': hora_bloque1_str,
                'hora_fin': (hora_bloque1_dt + timedelta(minutes=30)).strftime('%H:%M'),
                'cancha_id': cancha_seleccionada['id'],
                'cancha_nombre': cancha_seleccionada['nombre'],
                'cancha_tipo': cancha_seleccionada.get('tipo', 'N/A'),
                'cancha_condicion': cancha_seleccionada.get('condicion', 'N/A'),
                'cancha_monto': cancha_seleccionada.get('monto', 0) / 2
            }
            reservas.append(nueva_reserva1)
            
            nueva_reserva2 = {
                'id': max_id + 2,
                'clave_agrupacion': clave_agrupacion,
                'usuario': usuario,
                'fecha': fecha_bloque2,
                'hora_inicio': hora_bloque2_str,
                'hora_fin': hora_fin_str,
                'cancha_id': cancha_seleccionada['id'],
                'cancha_nombre': cancha_seleccionada['nombre'],
                'cancha_tipo': cancha_seleccionada.get('tipo', 'N/A'),
                'cancha_condicion': cancha_seleccionada.get('condicion', 'N/A'),
                'cancha_monto': cancha_seleccionada.get('monto', 0) / 2
            }
            reservas.append(nueva_reserva2)
            
            guardar_datos_json(RESERVAS_FILE, reservas)
            flash('Turno reservado exitosamente.', 'success')
            return redirect(url_for('mis_turnos'))

        except (ValueError, KeyError) as e:
            flash(f'Error en la reserva. Por favor, revisa los datos: {e}', 'error')
            return redirect(url_for('reservar_turno'))

    canchas = cargar_datos_json(CANCHAS_FILE)
    return render_template('reservar_turno.html', canchas=canchas)

@app.route('/api/turnos_disponibles/<fecha>')
def api_turnos_disponibles(fecha):
    try:
        if 'rol' not in session or session['rol'] != 'usuario':
            return jsonify({'error': 'No autorizado'}), 403

        reservas = cargar_datos_json(RESERVAS_FILE)
        canchas = cargar_datos_json(CANCHAS_FILE)

        # Crear un diccionario de horarios ocupados por cancha
        horarios_ocupados = defaultdict(set)
        
        for reserva in reservas:
            if reserva['fecha'] == fecha:
                # Agregar ambos bloques de 30 minutos como ocupados
                hora_inicio = reserva['hora_inicio']
                hora_bloque1 = datetime.strptime(hora_inicio, '%H:%M').strftime('%H:%M')
                hora_bloque2 = (datetime.strptime(hora_inicio, '%H:%M') + timedelta(minutes=30)).strftime('%H:%M')
                horarios_ocupados[reserva['cancha_id']].add(hora_bloque1)
                horarios_ocupados[reserva['cancha_id']].add(hora_bloque2)

        # Preparar la respuesta
        horarios_disponibles = {}
        for cancha in canchas:
            cancha_id = cancha['id']
            horarios_disponibles[cancha_id] = []
            
            # Generar horarios posibles (de 14:00 a 23:00 en intervalos de 1 hora)
            for hora in range(14, 23):
                hora_inicio = f"{hora:02d}:00"
                hora_fin = f"{hora+1:02d}:00"
                
                # Verificar disponibilidad de ambos bloques de 30 minutos
                hora_bloque1 = hora_inicio
                hora_bloque2 = (datetime.strptime(hora_inicio, '%H:%M') + timedelta(minutes=30)).strftime('%H:%M')
                
                if (hora_bloque1 not in horarios_ocupados.get(cancha_id, set()) and 
                    hora_bloque2 not in horarios_ocupados.get(cancha_id, set())):
                    horarios_disponibles[cancha_id].append({
                        'hora_inicio': hora_inicio,
                        'hora_fin': hora_fin
                    })

        return jsonify({
            'canchas': canchas,
            'horarios_disponibles': horarios_disponibles
        })

    except Exception as e:
        app.logger.error(f"Error en api_turnos_disponibles: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/mis_turnos')
def mis_turnos():
    if 'rol' not in session or session['rol'] != 'usuario':
        flash('Debes iniciar sesión como usuario para ver tus turnos.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))

    usuario = session['nombre_usuario']
    reservas = cargar_datos_json(RESERVAS_FILE)
    
    # Agrupar las reservas de 30 minutos en turnos de 1 hora para visualización
    mis_reservas_agrupadas = defaultdict(dict)
    for r in sorted(reservas, key=lambda x: (x['fecha'], x['hora_inicio'])):
        if r['usuario'] == usuario:
            clave = r['clave_agrupacion']
            if clave not in mis_reservas_agrupadas:
                mis_reservas_agrupadas[clave] = {
                    'fecha': r['fecha'],
                    'cancha_id': r['cancha_id'],
                    'cancha_nombre': r['cancha_nombre'],
                    'cancha_tipo': r.get('cancha_tipo', 'N/A'),
                    'cancha_condicion': r.get('cancha_condicion', 'N/A'),
                    'monto': 0,
                    'bloques': [],
                    'id': r['id'],
                    'clave_agrupacion': clave,
                    'hora_inicio': r['hora_inicio'],
                    'hora_fin': ''
                }
            mis_reservas_agrupadas[clave]['bloques'].append(r)
            mis_reservas_agrupadas[clave]['monto'] += r['cancha_monto']
            mis_reservas_agrupadas[clave]['hora_fin'] = r['hora_fin']
    
    mis_reservas_list = sorted(list(mis_reservas_agrupadas.values()), 
                               key=lambda x: (x['fecha'], x['hora_inicio']))

    return render_template('mis_turnos.html', mis_turnos=mis_reservas_list)

@app.route('/cancelar_turno/<int:reserva_id>')
def cancelar_turno(reserva_id):
    if 'rol' not in session or session['rol'] != 'usuario':
        flash('Debes iniciar sesión como usuario para cancelar un turno.', 'error')
        return redirect(url_for('iniciar_sesion_usuario'))
    
    usuario = session['nombre_usuario']
    reservas = cargar_datos_json(RESERVAS_FILE)
    
    # Buscar el primer bloque de la reserva a cancelar
    reserva_a_cancelar = next((r for r in reservas if r['id'] == reserva_id and r['usuario'] == usuario), None)
    
    if reserva_a_cancelar:
        clave_agrupacion = reserva_a_cancelar['clave_agrupacion']
        
        # Encontrar y eliminar todos los bloques con la misma clave de agrupación
        reservas_a_eliminar = [r for r in reservas if r['clave_agrupacion'] == clave_agrupacion]
        
        # Guardar en el archivo de canceladas
        reservas_canceladas = cargar_datos_json(RESERVAS_CANCELADAS_FILE)
        reservas_canceladas.extend(reservas_a_eliminar)
        guardar_datos_json(RESERVAS_CANCELADAS_FILE, reservas_canceladas)
        
        # Crear una nueva lista de reservas sin las eliminadas
        reservas_filtradas = [r for r in reservas if r['clave_agrupacion'] != clave_agrupacion]
        guardar_datos_json(RESERVAS_FILE, reservas_filtradas)
        
        flash('Turno cancelado exitosamente.', 'success')
    else:
        flash('No se pudo encontrar o cancelar el turno.', 'error')
        
    return redirect(url_for('mis_turnos'))

# --- RUTAS PARA LA GESTIÓN DE CANCHAS (ADMIN) ---

@app.route('/gestionar_canchas')
def gestionar_canchas():
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    canchas = cargar_datos_json(CANCHAS_FILE)
    return render_template('gestionar_canchas.html', canchas=canchas)

@app.route('/agregar_cancha', methods=['GET', 'POST'])
def agregar_cancha():
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        condicion = request.form['condicion']
        monto_str = request.form['monto']
        
        canchas = cargar_datos_json(CANCHAS_FILE)
        
        if any(c.get('nombre') == nombre for c in canchas):
            flash('Ya existe una cancha con ese nombre.', 'error')
            return redirect(url_for('agregar_cancha'))
            
        try:
            monto = float(monto_str)
        except ValueError:
            flash('El monto debe ser un número válido.', 'error')
            return redirect(url_for('agregar_cancha'))
            
        max_id = max([c['id'] for c in canchas]) if canchas else 0
        canchas.append({
            'id': max_id + 1,
            'nombre': nombre,
            'tipo': tipo,
            'condicion': condicion,
            'monto': monto
        })
        guardar_datos_json(CANCHAS_FILE, canchas)
        flash('Cancha agregada exitosamente.', 'success')
        return redirect(url_for('gestionar_canchas'))
    
    return render_template('agregar_cancha.html')

@app.route('/editar_cancha/<int:cancha_id>', methods=['GET', 'POST'])
def editar_cancha(cancha_id):
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    canchas = cargar_datos_json(CANCHAS_FILE)
    cancha_a_editar = next((c for c in canchas if c.get('id') == cancha_id), None)
    
    if not cancha_a_editar:
        flash('Cancha no encontrada.', 'error')
        return redirect(url_for('gestionar_canchas'))
        
    if request.method == 'POST':
        nuevo_nombre = request.form['nombre']
        nuevo_tipo = request.form['tipo']
        nueva_condicion = request.form['condicion']
        nuevo_monto_str = request.form['monto']

        if any(c.get('nombre') == nuevo_nombre for c in canchas if c.get('id') != cancha_id):
            flash('Ya existe otra cancha con ese nombre.', 'error')
            return redirect(url_for('editar_cancha', cancha_id=cancha_id))
            
        try:
            nuevo_monto = float(nuevo_monto_str)
        except ValueError:
            flash('El monto debe ser un número válido.', 'error')
            return redirect(url_for('editar_cancha', cancha_id=cancha_id))

        cancha_a_editar['nombre'] = nuevo_nombre
        cancha_a_editar['tipo'] = nuevo_tipo
        cancha_a_editar['condicion'] = nueva_condicion
        cancha_a_editar['monto'] = nuevo_monto
        
        guardar_datos_json(CANCHAS_FILE, canchas)
        flash('Cancha actualizada exitosamente.', 'success')
        return redirect(url_for('gestionar_canchas'))
    
    return render_template('editar_cancha.html', cancha=cancha_a_editar)

@app.route('/eliminar_cancha/<int:cancha_id>')
def eliminar_cancha(cancha_id):
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    canchas = cargar_datos_json(CANCHAS_FILE)
    cancha_a_eliminar = next((c for c in canchas if c.get('id') == cancha_id), None)
    
    if cancha_a_eliminar:
        canchas.remove(cancha_a_eliminar)
        guardar_datos_json(CANCHAS_FILE, canchas)
        flash('Cancha eliminada exitosamente.', 'success')
    else:
        flash('Cancha no encontrada.', 'error')
        
    return redirect(url_for('gestionar_canchas'))

# --- RUTAS MEJORADAS PARA EL ADMINISTRADOR ---

@app.route('/ver_turnos_administrador')
def ver_turnos_administrador():
    try:
        # Verificar sesión admin
        if 'rol' not in session or session['rol'] != 'administrador':
            flash('Acceso no autorizado', 'error')
            return redirect(url_for('iniciar_sesion_administrador'))

        # Cargar reservas con manejo de errores
        reservas = cargar_datos_json(RESERVAS_FILE)
        if not isinstance(reservas, list):
            reservas = []
            print("Advertencia: Las reservas no son una lista válida")

        # Agrupar por clave_agrupacion
        grupos = defaultdict(list)
        for reserva in reservas:
            try:
                clave = reserva['clave_agrupacion']
                grupos[clave].append(reserva)
            except KeyError:
                print(f"Reserva sin clave_agrupacion: {reserva.get('id')}")
                continue

        # Procesar cada grupo de reservas (2 bloques de 30 min)
        turnos_procesados = []
        for clave, bloques in grupos.items():
            try:
                bloques_ordenados = sorted(bloques, key=lambda x: x['hora_inicio'])
                
                # Validar que sean exactamente 2 bloques consecutivos
                if len(bloques_ordenados) == 2:
                    primer_bloque = bloques_ordenados[0]
                    segundo_bloque = bloques_ordenados[1]
                    
                    # Verificar que sean consecutivos
                    hora_fin_primer = datetime.strptime(primer_bloque['hora_fin'], '%H:%M')
                    hora_inicio_segundo = datetime.strptime(segundo_bloque['hora_inicio'], '%H:%M')
                    
                    if hora_fin_primer == hora_inicio_segundo:
                        turno = {
                            'id': primer_bloque['id'],
                            'fecha': primer_bloque['fecha'],
                            'hora_inicio': primer_bloque['hora_inicio'],
                            'hora_fin': segundo_bloque['hora_fin'],
                            'cancha_nombre': primer_bloque['cancha_nombre'],
                            'usuario': primer_bloque['usuario'],
                            'monto_total': primer_bloque['cancha_monto'] + segundo_bloque['cancha_monto'],
                            'clave_agrupacion': clave
                        }
                        turnos_procesados.append(turno)
                    else:
                        print(f"Bloques no consecutivos en reserva {clave}")
                else:
                    print(f"Grupo incompleto en reserva {clave} - Bloques: {len(bloques_ordenados)}")
            
            except Exception as e:
                print(f"Error procesando grupo {clave}: {str(e)}")
                continue

        # Ordenar por fecha y hora
        turnos_procesados.sort(key=lambda x: (x['fecha'], x['hora_inicio']))

        # Agrupar por fecha para el template
        reservas_por_dia = defaultdict(list)
        for turno in turnos_procesados:
            reservas_por_dia[turno['fecha']].append(turno)

        return render_template('ver_turnos_administrador.html',
                           reservas_por_dia=sorted(reservas_por_dia.items()))

    except Exception as e:
        print(f"Error crítico en ver_turnos_administrador: {str(e)}")
        flash('Error interno al mostrar los turnos', 'error')
        return render_template('ver_turnos_administrador.html', reservas_por_dia=[])

@app.route('/cancelar_turno_admin/<int:reserva_id>')
def cancelar_turno_admin(reserva_id):
    try:
        if 'rol' not in session or session['rol'] != 'administrador':
            flash('Acceso no autorizado', 'error')
            return redirect(url_for('iniciar_sesion_administrador'))

        # Cargar datos
        reservas = cargar_datos_json(RESERVAS_FILE) or []
        reservas_canceladas = cargar_datos_json(RESERVAS_CANCELADAS_FILE) or []

        # Encontrar la reserva específica
        reserva = next((r for r in reservas if r['id'] == reserva_id), None)
        if not reserva:
            flash('Turno no encontrado', 'error')
            return redirect(url_for('ver_turnos_administrador'))

        # Mover todos los bloques con la misma clave_agrupacion
        clave = reserva['clave_agrupacion']
        reservas_a_cancelar = [r for r in reservas if r['clave_agrupacion'] == clave]
        
        if not reservas_a_cancelar:
            flash('No se encontraron bloques para cancelar', 'error')
            return redirect(url_for('ver_turnos_administrador'))

        # Actualizar listas
        nuevas_reservas = [r for r in reservas if r['clave_agrupacion'] != clave]
        reservas_canceladas.extend(reservas_a_cancelar)

        # Guardar cambios
        guardar_datos_json(RESERVAS_FILE, nuevas_reservas)
        guardar_datos_json(RESERVAS_CANCELADAS_FILE, reservas_canceladas)

        flash(f'Turno cancelado exitosamente (ID: {reserva_id})', 'success')
        return redirect(url_for('ver_turnos_administrador'))

    except Exception as e:
        print(f"Error al cancelar turno: {str(e)}")
        flash('Error interno al cancelar el turno', 'error')
        return redirect(url_for('ver_turnos_administrador'))

@app.route('/gestionar_usuarios')
def gestionar_usuarios():
    error_redirect = verificar_admin()
    if error_redirect: return error_redirect
    
    usuarios_normales = cargar_datos_json(USUARIOS_NORMAL_FILE)
    administradores = cargar_datos_json(USUARIOS_ADMIN_FILE)

    return render_template('gestionar_usuarios.html', usuarios=usuarios_normales, administradores=administradores)

@app.route('/ver_turnos_cancelados_administrador')
def ver_turnos_cancelados_administrador():
    try:
        # Verificar sesión de administrador
        if 'rol' not in session or session['rol'] != 'administrador':
            flash('Acceso denegado', 'error')
            return redirect(url_for('iniciar_sesion_administrador'))

        # Cargar reservas canceladas con manejo robusto
        try:
            reservas_canceladas = cargar_datos_json(RESERVAS_CANCELADAS_FILE)
            if not isinstance(reservas_canceladas, list):
                reservas_canceladas = []
        except Exception as e:
            print(f"Error al cargar reservas canceladas: {str(e)}")
            reservas_canceladas = []

        # Agrupar por fecha
        reservas_por_dia = defaultdict(list)
        
        # Primero agrupar por clave_agrupacion para juntar los bloques de 30min
        grupos = defaultdict(list)
        for reserva in reservas_canceladas:
            grupos[reserva['clave_agrupacion']].append(reserva)
        
        # Procesar cada grupo de reservas
        for clave, bloques in grupos.items():
            bloques_ordenados = sorted(bloques, key=lambda x: x['hora_inicio'])
            
            if len(bloques_ordenados) >= 1:  # Aunque sea 1 bloque
                primer_bloque = bloques_ordenados[0]
                fecha = primer_bloque['fecha']
                
                turno = {
                    'fecha': fecha,
                    'hora_inicio': primer_bloque['hora_inicio'],
                    'hora_fin': bloques_ordenados[-1]['hora_fin'],
                    'cancha_nombre': primer_bloque.get('cancha_nombre', 'Cancha Desconocida'),
                    'usuario': primer_bloque.get('usuario', 'Anónimo'),
                    'monto_total': sum(b.get('cancha_monto', 0) for b in bloques_ordenados),
                    'fecha_cancelacion': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'id': primer_bloque['id']
                }
                
                reservas_por_dia[fecha].append(turno)

        # Ordenar las fechas
        reservas_por_dia = dict(sorted(reservas_por_dia.items(), reverse=True))
        
        # Ordenar los turnos dentro de cada fecha
        for fecha in reservas_por_dia:
            reservas_por_dia[fecha].sort(key=lambda x: x['hora_inicio'])

        return render_template('ver_turnos_cancelados_administrador.html',
                           reservas_por_dia=reservas_por_dia.items())

    except Exception as e:
        print(f"Error en ver_turnos_cancelados: {str(e)}")
        flash('Error al cargar turnos cancelados', 'error')
        return render_template('ver_turnos_cancelados_administrador.html',
                           reservas_por_dia=[])
    
@app.route('/informe_financiero_administrador')
def informe_financiero_administrador():
    try:
        # Verificar sesión de administrador
        if 'rol' not in session or session['rol'] != 'administrador':
            flash('Acceso denegado', 'error')
            return redirect(url_for('iniciar_sesion_administrador'))

        # Cargar solo reservas activas
        reservas = cargar_datos_json(RESERVAS_FILE) or []
        
        # Inicializar estructuras para los informes
        ingresos = {
            'diarios': defaultdict(float),
            'semanales': defaultdict(float),
            'mensuales': defaultdict(float),
            'trimestrales': defaultdict(float),
            'semestrales': defaultdict(float),
            'anuales': defaultdict(float)
        }

        # Procesar cada reserva
        for reserva in reservas:
            try:
                fecha = datetime.strptime(reserva['fecha'], '%Y-%m-%d')
                monto = float(reserva.get('cancha_monto', 0))
                
                # Agrupar por clave_agrupacion para evitar duplicados
                if reserva['hora_inicio'].endswith('00'):  # Solo procesamos el primer bloque de cada hora
                    # Ingresos diarios
                    ingresos['diarios'][reserva['fecha']] += monto * 2  # Sumamos los 2 bloques
                    
                    # Ingresos semanales
                    semana = f"{fecha.year}-Semana {fecha.isocalendar()[1]}"
                    ingresos['semanales'][semana] += monto * 2
                    
                    # Ingresos mensuales
                    mes = f"{fecha.year}-{fecha.month:02d}"
                    ingresos['mensuales'][mes] += monto * 2
                    
                    # Ingresos trimestrales
                    trimestre = f"{fecha.year}-T{(fecha.month-1)//3 + 1}"
                    ingresos['trimestrales'][trimestre] += monto * 2
                    
                    # Ingresos semestrales
                    semestre = f"{fecha.year}-S{1 if fecha.month <= 6 else 2}"
                    ingresos['semestrales'][semestre] += monto * 2
                    
                    # Ingresos anuales
                    ingresos['anuales'][str(fecha.year)] += monto * 2
            except (ValueError, KeyError) as e:
                print(f"Error procesando reserva {reserva.get('id')}: {str(e)}")
                continue

        # Convertir a listas ordenadas
        reportes = {
            'diario': sorted(ingresos['diarios'].items(), reverse=True),
            'semanal': sorted(ingresos['semanales'].items(), reverse=True),
            'mensual': sorted(ingresos['mensuales'].items(), reverse=True),
            'trimestral': sorted(ingresos['trimestrales'].items(), reverse=True),
            'semestral': sorted(ingresos['semestrales'].items(), reverse=True),
            'anual': sorted(ingresos['anuales'].items(), reverse=True)
        }

        return render_template('informe_financiero_administrador.html', 
                            reportes=reportes)

    except Exception as e:
        print(f"Error en informe financiero: {str(e)}")
        flash('Error al generar el informe', 'error')
        return render_template('informe_financiero_administrador.html', 
                            reportes={})

# --- Final de la aplicación ---
if __name__ == '__main__':
    os.makedirs(CARPETA_DATOS, exist_ok=True)
    if not os.path.exists(USUARIOS_ADMIN_FILE):
        guardar_datos_json(USUARIOS_ADMIN_FILE, [])
    if not os.path.exists(USUARIOS_NORMAL_FILE):
        guardar_datos_json(USUARIOS_NORMAL_FILE, [])
    if not os.path.exists(RESERVAS_FILE):
        guardar_datos_json(RESERVAS_FILE, [])
    if not os.path.exists(CANCHAS_FILE):
        guardar_datos_json(CANCHAS_FILE, [])
    if not os.path.exists(RESERVAS_CANCELADAS_FILE):
        guardar_datos_json(RESERVAS_CANCELADAS_FILE, [])
    
    app.run(debug=False, use_reloader=False)