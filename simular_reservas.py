import os
import random
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

# --- IMPORTANTE: Importamos la app y los modelos de la DB ---
from app import app, db, Usuario, Cancha, Reserva

# --- La función crear_canchas_iniciales() se ha eliminado ---
# --- La función crear_usuarios_iniciales() se ha eliminado ---


def generar_simulacion(usuarios_disponibles, canchas_db, fecha_simulacion, total_reservas=14):
    """
    Genera una simulación de reservas (LÓGICA DE 1 HORA)
    Respeta la regla de 1 usuario/semana y 14 reservas/día.
    """
    
    # Lógica de 14 reservas totales (9-10 activas, 4-5 canceladas)
    reservas_activas_count = random.randint(9, 10) 
    reservas_a_cancelar_count = total_reservas - reservas_activas_count

    # Horarios (14:00 a 22:00)
    horarios_preferentes = [f"{h:02d}:00" for h in range(17, 21)]
    horarios_normales = [f"{h:02d}:00" for h in range(14, 17)] + [f"{h:02d}:00" for h in range(21, 23)]

    nuevas_reservas_generadas = []
    horas_inicio_reservas = []
    turnos_ocupados = set()
    
    # Hacemos una copia de la lista de usuarios disponibles para este día
    usuarios_para_hoy = list(usuarios_disponibles)
    usuarios_usados_en_esta_sim = set() # Guarda los IDs de los usuarios usados

    i = 0
    intentos = 0
    while i < total_reservas and intentos < 1000:
        intentos += 1
        
        if not usuarios_para_hoy:
            print(f"Advertencia: No hay más usuarios únicos disponibles para {fecha_simulacion}. Se generaron {i} reservas.")
            break
        
        usuario = random.choice(usuarios_para_hoy)
        cancha = random.choice(canchas_db)
        
        if random.random() < 0.7:
            hora_inicio = random.choice(horarios_preferentes)
        else:
            hora_inicio = random.choice(horarios_normales)
        
        clave_turno = (fecha_simulacion, cancha.id, hora_inicio)
        if clave_turno in turnos_ocupados:
            continue 

        turnos_ocupados.add(clave_turno)
        horas_inicio_reservas.append(hora_inicio)
        
        usuarios_usados_en_esta_sim.add(usuario.id)
        usuarios_para_hoy.remove(usuario)

        hora_inicio_dt = datetime.strptime(hora_inicio, '%H:%M')
        hora_fin_str = (hora_inicio_dt + timedelta(hours=1)).strftime('%H:%M')
        
        reserva = Reserva(
            usuario_id=usuario.id,
            cancha_id=cancha.id,
            fecha=fecha_simulacion,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin_str,
            monto=cancha.monto,
            estado='activa' 
        )
        
        nuevas_reservas_generadas.append(reserva)
        i += 1 

    total_generadas = len(nuevas_reservas_generadas)
    if reservas_a_cancelar_count > total_generadas:
        reservas_a_cancelar_count = total_generadas // 2

    # Seleccionar reservas a cancelar y cambiar su estado
    reservas_canceladas_final = random.sample(nuevas_reservas_generadas, reservas_a_cancelar_count)
    reservas_activas_final = []
    
    for r in nuevas_reservas_generadas:
        if r in reservas_canceladas_final:
            r.estado = 'cancelada' 
        else:
            reservas_activas_final.append(r)
            
    conteo_horarios = defaultdict(int)
    for hora in horas_inicio_reservas:
        conteo_horarios[hora] += 1
    
    horarios_populares = sorted(
        conteo_horarios.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:3]
    
    estadisticas = {
        'fecha': fecha_simulacion,
        'total_reservas': total_generadas,
        'reservas_activas': len(reservas_activas_final),
        'reservas_canceladas': len(reservas_canceladas_final),
        'horarios_populares': horarios_populares,
        'reservas_para_db': nuevas_reservas_generadas, 
        'usuarios_usados': usuarios_usados_en_esta_sim 
    }
    
    return estadisticas

def mostrar_resumen(estadisticas):
    """Muestra el resumen de la simulación generada"""
    print("\n" + "="*50)
    print("Resumen de simulación generada:")
    print(f"- Fecha objetivo: {estadisticas['fecha']}")
    print(f"- Total reservas: {estadisticas['total_reservas']}")
    print(f"- Reservas activas: {estadisticas['reservas_activas']}")
    print(f"- Reservas a cancelar: {estadisticas['reservas_canceladas']}")
    print("\nHorarios más populares:")
    for hora, cantidad in estadisticas['horarios_populares']:
        print(f"  - {hora}: {cantidad} reservas")
    print("="*50)

def obtener_fecha_simulacion():
    """Pide al usuario la fecha para la simulación con validación"""
    while True:
        fecha_input = input("\nIngrese la fecha para simular (formato YYYY-MM-DD) o presione Enter para hoy: ").strip()
        
        if not fecha_input:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            datetime.strptime(fecha_input, '%Y-%m-%d')
            return fecha_input
        except ValueError:
            print("Formato de fecha inválido. Use YYYY-MM-DD (ej: 2023-12-31)")

def obtener_mes_simulacion():
    """Pide al usuario el mes y año para la simulación mensual"""
    while True:
        mes_input = input("\nIngrese el mes y año para simular (formato YYYY-MM) o presione Enter para el mes actual: ").strip()
        
        if not mes_input:
            return datetime.now().strftime('%Y-%m')
        
        try:
            datetime.strptime(mes_input + '-01', '%Y-%m-%d')
            return mes_input
        except ValueError:
            print("Formato inválido. Use YYYY-MM (ej: 2023-12)")

def generar_reservas_mensual(usuarios_db, canchas_db):
    """Genera reservas simuladas para todos los días de un mes"""
    mes_simulacion = obtener_mes_simulacion()
    print(f"\nMes seleccionado para simulación: {mes_simulacion}")
    
    confirmar = input(f"¿Está seguro de generar simulaciones para todo {mes_simulacion}? [s]í / [n]o: ").strip().lower()
    if confirmar != 's':
        print("Operación cancelada.")
        return

    año, mes = map(int, mes_simulacion.split('-'))
    num_dias = calendar.monthrange(año, mes)[1]
    
    reservas_para_db = []
    
    print(f"\nGenerando simulaciones para {mes_simulacion}...")
    
    semana_actual = -1
    usuarios_usados_esta_semana = set()
    
    for dia in range(1, num_dias + 1):
        fecha_actual_dt = datetime(año, mes, dia)
        fecha_actual = fecha_actual_dt.strftime('%Y-%m-%d')
        
        num_semana = fecha_actual_dt.isocalendar().week
        if num_semana != semana_actual:
            print(f"--- Nueva Semana ({num_semana}) - Reseteando usuarios ---")
            usuarios_usados_esta_semana.clear()
            semana_actual = num_semana
        
        if fecha_actual_dt < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            print(f"Saltando día {fecha_actual} (fecha pasada)")
            continue
            
        print(f"Simulando {fecha_actual}")
        
        usuarios_disponibles = [u for u in usuarios_db if u.id not in usuarios_usados_esta_semana]
        if not usuarios_disponibles:
            print(f"No hay más usuarios únicos disponibles para esta semana. Saltando día.")
            continue

        total_reservas_dia = 14
        estadisticas = generar_simulacion(usuarios_disponibles, canchas_db, fecha_actual, total_reservas_dia)
        
        if not estadisticas:
            print(f"Error al generar simulación para {fecha_actual}.")
            continue
            
        reservas_para_db.extend(estadisticas['reservas_para_db'])
        usuarios_usados_esta_semana.update(estadisticas['usuarios_usados'])
    
    print(f"\nGuardando {len(reservas_para_db)} reservas en la base de datos...")
    db.session.add_all(reservas_para_db)
    db.session.commit()

    print(f"\nSimulación mensual completada para {mes_simulacion}!")
    print(f"- Total de reservas generadas: {len(reservas_para_db)}")

def generar_reservas_anual(usuarios_db, canchas_db):
    """Genera reservas simuladas para los últimos 365 días hasta hoy"""
    
    print("\nSimulación ANUAL: Se generarán 14 reservas por día para los últimos 365 días.")
    confirmar = input(f"Esto generará {14*365} reservas (aprox 5k) y tardará unos segundos. ¿Está seguro? [s]í / [n]o: ").strip().lower()
    if confirmar != 's':
        print("Operación cancelada.")
        return

    reservas_para_db = []
    
    today = datetime.now()
    start_date = today - timedelta(days=365)
    total_dias = (today - start_date).days
    
    print(f"\nGenerando simulaciones para los últimos {total_dias} días...")
    
    semana_actual = -1
    usuarios_usados_esta_semana = set()
    
    current_date = start_date
    while current_date <= today:
        fecha_simulacion = current_date.strftime('%Y-%m-%d')
        
        num_semana = current_date.isocalendar().week
        if num_semana != semana_actual:
            print(f"--- Nueva Semana ({num_semana}) - Reseteando usuarios ---")
            usuarios_usados_esta_semana.clear()
            semana_actual = num_semana
            
        print(f"Simulando {fecha_simulacion}...")
        
        usuarios_disponibles = [u for u in usuarios_db if u.id not in usuarios_usados_esta_semana]
        if not usuarios_disponibles:
            print(f"No hay más usuarios únicos disponibles para esta semana. Saltando día.")
            current_date += timedelta(days=1)
            continue
            
        total_reservas_dia = 14
        estadisticas = generar_simulacion(usuarios_disponibles, canchas_db, fecha_simulacion, total_reservas_dia)
        
        if not estadisticas:
            print(f"Error al generar simulación para {fecha_simulacion}.")
            current_date += timedelta(days=1)
            continue
            
        reservas_para_db.extend(estadisticas['reservas_para_db'])
        usuarios_usados_esta_semana.update(estadisticas['usuarios_usados'])
        
        current_date += timedelta(days=1)
    
    print(f"\nGuardando {len(reservas_para_db)} reservas en la base de datos...")
    db.session.add_all(reservas_para_db)
    db.session.commit()

    print(f"\nSimulación ANUAL completada!")
    print(f"- Total de días simulados: {total_dias + 1}")
    print(f"- Total de reservas generadas: {len(reservas_para_db)}")

def generar_reservas_simuladas(app_context):
    with app_context:
        # --- CARGAMOS LOS DATOS EXISTENTES DE LA DB ---
        print("Cargando datos de la base de datos...")
        usuarios_db = Usuario.query.all()
        canchas_db = Cancha.query.all()

        if not usuarios_db or len(usuarios_db) < 100:
            print(f"Error: No se encontraron suficientes usuarios ({len(usuarios_db)}). Se necesitan 100+.")
            print("Por favor, ejecuta 'python crear_usuarios.py' primero.")
            return

        if not canchas_db:
            print("Error: No hay canchas disponibles en la base de datos.")
            return
        
        print(f"Datos cargados: {len(usuarios_db)} usuarios, {len(canchas_db)} canchas.")
        
        # Pedir tipo de simulación
        while True:
            tipo = input("\n¿Qué tipo de simulación desea? [d]ía / [m]ensual / [a]nual: ").strip().lower()
            
            if tipo == 'd':
                fecha_simulacion = obtener_fecha_simulacion()
                print(f"\nFecha seleccionada para simulación: {fecha_simulacion}")
                
                if len(usuarios_db) < 14:
                     print("Error: Se necesitan al menos 14 usuarios en la DB para simular un día.")
                     break
                
                usuarios_disponibles = random.sample(usuarios_db, 14)
                
                while True:
                    estadisticas = generar_simulacion(usuarios_disponibles, canchas_db, fecha_simulacion, 14) 
                    mostrar_resumen(estadisticas)
                    
                    opcion = input("\nOpciones: [s] Confirmar y guardar, [n] Generar nueva, [c] Cambiar fecha, [q] Salir\nSeleccione: ").strip().lower()
                    
                    if opcion == 's':
                        print(f"Guardando {len(estadisticas['reservas_para_db'])} reservas en la base de datos...")
                        db.session.add_all(estadisticas['reservas_para_db'])
                        db.session.commit()
                        print("\nSimulación guardada exitosamente!")
                        break
                    elif opcion == 'n':
                        print("\nGenerando nueva simulación para la misma fecha...")
                        continue
                    elif opcion == 'c':
                        fecha_simulacion = obtener_fecha_simulacion()
                        print(f"\nFecha cambiada a: {fecha_simulacion}")
                        continue
                    elif opcion == 'q':
                        print("\nOperación cancelada.")
                        break
                    else:
                        print("\nOpción no válida.")
                break
                
            elif tipo == 'm':
                generar_reservas_mensual(usuarios_db, canchas_db)
                break
            
            elif tipo == 'a':
                generar_reservas_anual(usuarios_db, canchas_db)
                break
                
            else:
                print("Opción no válida. Por favor seleccione d, m o a.")

if __name__ == '__main__':
    app_context = app.app_context()
    generar_reservas_simuladas(app_context)