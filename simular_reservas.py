import os
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict

# Configuración de rutas
CARPETA_DATOS = os.path.join(os.path.dirname(__file__), 'datos')
USUARIOS_NORMAL_FILE = os.path.join(CARPETA_DATOS, 'usuarios.json')
RESERVAS_FILE = os.path.join(CARPETA_DATOS, 'reservas.json')
CANCHAS_FILE = os.path.join(CARPETA_DATOS, 'canchas.json')
RESERVAS_CANCELADAS_FILE = os.path.join(CARPETA_DATOS, 'reservas_canceladas.json')

def cargar_datos(filepath):
    """Carga datos desde un archivo JSON"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_datos(filepath, data):
    """Guarda datos en un archivo JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def generar_simulacion(usuarios, canchas, fecha_simulacion, max_id, total_reservas=28):  # Cambiado a 28
    """Genera una simulación de reservas sin guardar"""
    # Configuración de la simulación (ajustado para 4-7 cancelaciones)
    reservas_activas = random.randint(21, 24)  # 28 - 21 = 7, 28 - 24 = 4
    reservas_a_cancelar = total_reservas - reservas_activas

    # Horarios preferentes (17:00-21:00) y normales (14:00-16:59, 21:01-22:00)
    horarios_preferentes = [f"{h:02d}:00" for h in range(17, 21)]
    horarios_normales = [f"{h:02d}:00" for h in range(14, 17)] + [f"{h:02d}:00" for h in range(21, 23)]

    # Generar reservas
    nuevas_reservas = []
    horas_inicio_reservas = []  # Para estadísticas

    for i in range(total_reservas):
        # Seleccionar usuario y cancha aleatoria
        usuario = random.choice(usuarios)['nombre_usuario']
        cancha = random.choice(canchas)
        
        # Seleccionar horario (70% probabilidad en horario preferente)
        if random.random() < 0.7:
            hora_inicio = random.choice(horarios_preferentes)
        else:
            hora_inicio = random.choice(horarios_normales)
        
        # Registrar hora para estadísticas
        horas_inicio_reservas.append(hora_inicio)
        
        # Crear clave de agrupación única
        clave_agrupacion = f"simulada-{usuario}-{fecha_simulacion}-{hora_inicio}-{cancha['id']}"
        
        # Crear los dos bloques de 30 minutos
        hora_inicio_dt = datetime.strptime(hora_inicio, '%H:%M')
        hora_bloque1_str = hora_inicio_dt.strftime('%H:%M')
        hora_bloque2_str = (hora_inicio_dt + timedelta(minutes=30)).strftime('%H:%M')
        hora_fin_str = (hora_inicio_dt + timedelta(hours=1)).strftime('%H:%M')
        
        # Crear bloques de reserva
        bloque1 = {
            'id': max_id + 1 + (i * 2),
            'clave_agrupacion': clave_agrupacion,
            'usuario': usuario,
            'fecha': fecha_simulacion,
            'hora_inicio': hora_bloque1_str,
            'hora_fin': hora_bloque2_str,
            'cancha_id': cancha['id'],
            'cancha_nombre': cancha['nombre'],
            'cancha_tipo': cancha.get('tipo', 'N/A'),
            'cancha_condicion': cancha.get('condicion', 'N/A'),
            'cancha_monto': cancha.get('monto', 0) / 2
        }
        
        bloque2 = {
            'id': max_id + 2 + (i * 2),
            'clave_agrupacion': clave_agrupacion,
            'usuario': usuario,
            'fecha': fecha_simulacion,
            'hora_inicio': hora_bloque2_str,
            'hora_fin': hora_fin_str,
            'cancha_id': cancha['id'],
            'cancha_nombre': cancha['nombre'],
            'cancha_tipo': cancha.get('tipo', 'N/A'),
            'cancha_condicion': cancha.get('condicion', 'N/A'),
            'cancha_monto': cancha.get('monto', 0) / 2
        }
        
        nuevas_reservas.extend([bloque1, bloque2])

    # Seleccionar reservas a cancelar (aleatoriamente)
    reservas_por_clave = defaultdict(list)
    for reserva in nuevas_reservas:
        reservas_por_clave[reserva['clave_agrupacion']].append(reserva)
    
    claves_unicas = list(reservas_por_clave.keys())
    claves_a_cancelar = random.sample(claves_unicas, reservas_a_cancelar)

    # Separar en activas y canceladas
    reservas_activas_final = []
    reservas_canceladas_final = []
    
    for clave in claves_unicas:
        if clave in claves_a_cancelar:
            reservas_canceladas_final.extend(reservas_por_clave[clave])
        else:
            reservas_activas_final.extend(reservas_por_clave[clave])
    
    # Calcular estadísticas
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
        'total_reservas': total_reservas,
        'reservas_activas': reservas_activas,
        'reservas_canceladas': reservas_a_cancelar,
        'horarios_populares': horarios_populares,
        'reservas_activas_final': reservas_activas_final,
        'reservas_canceladas_final': reservas_canceladas_final
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
            # Usar fecha actual si no se ingresa nada
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Validar formato de fecha
            datetime.strptime(fecha_input, '%Y-%m-%d')
            return fecha_input
        except ValueError:
            print("Formato de fecha inválido. Use YYYY-MM-DD (ej: 2023-12-31)")

def generar_reservas_simuladas():
    # Cargar datos existentes
    usuarios = cargar_datos(USUARIOS_NORMAL_FILE)
    canchas = cargar_datos(CANCHAS_FILE)
    reservas = cargar_datos(RESERVAS_FILE)
    reservas_canceladas = cargar_datos(RESERVAS_CANCELADAS_FILE)

    if not usuarios:
        print("Error: No hay usuarios disponibles para generar reservas")
        return

    if not canchas:
        print("Error: No hay canchas disponibles para generar reservas")
        return

    # Configuración inicial
    max_id = max([r['id'] for r in reservas]) if reservas else 0
    total_reservas = 28  # Cambiado a 28 reservas diarias
    
    # Pedir fecha de simulación
    fecha_simulacion = obtener_fecha_simulacion()
    print(f"\nFecha seleccionada para simulación: {fecha_simulacion}")
    
    # Bucle principal para regenerar simulaciones
    while True:
        # Generar nueva simulación
        estadisticas = generar_simulacion(
            usuarios, canchas, fecha_simulacion, max_id, total_reservas
        )
        
        # Mostrar resumen
        mostrar_resumen(estadisticas)
        
        # Pedir confirmación
        opcion = input("\nOpciones: [s] Confirmar y guardar, [n] Generar nueva simulación, [c] Cambiar fecha, [q] Salir\nSeleccione: ").strip().lower()
        
        if opcion == 's':
            # Combinar con datos existentes
            todas_reservas = reservas + estadisticas['reservas_activas_final']
            todas_canceladas = reservas_canceladas + estadisticas['reservas_canceladas_final']

            # Guardar los datos
            guardar_datos(RESERVAS_FILE, todas_reservas)
            guardar_datos(RESERVAS_CANCELADAS_FILE, todas_canceladas)

            print("\nSimulación guardada exitosamente!")
            print(f"- Nuevas reservas activas: {len(estadisticas['reservas_activas_final'])} bloques")
            print(f"- Nuevas reservas canceladas: {len(estadisticas['reservas_canceladas_final'])} bloques")
            break
            
        elif opcion == 'n':
            print("\nGenerando nueva simulación para la misma fecha...")
            continue
            
        elif opcion == 'c':
            # Cambiar fecha de simulación
            fecha_simulacion = obtener_fecha_simulacion()
            print(f"\nFecha cambiada a: {fecha_simulacion}")
            print("Generando nueva simulación con la nueva fecha...")
            continue
            
        elif opcion == 'q':
            print("\nOperación cancelada. No se guardaron cambios.")
            break
            
        else:
            print("\nOpción no válida. Por favor seleccione s, n, c o q.")

if __name__ == '__main__':
    generar_reservas_simuladas()