import sys
import random
from datetime import datetime

# --- IMPORTACIÓN CLAVE ---
# Importamos la 'app' y la 'db' desde tu archivo principal app.py
# También importamos el modelo 'Gasto' que debe estar definido en app.py
try:
    from app import app, db, Gasto
except ImportError:
    print("Error: No se pudo encontrar 'app.py' o los modelos 'app', 'db', 'Gasto'.")
    print("Asegúrate de que este script esté en la misma carpeta que 'app.py' y que 'Gasto' esté definido.")
    sys.exit(1)

# --- LISTA DE GASTOS (Basada en lo que definimos) ---

# Gastos Fijos (12 veces al año)
GASTOS_MENSUALES = [
    {"cat": "Alquiler", "con": "Alquiler del Predio", "monto": 700000},
    {"cat": "Sueldos", "con": "Sueldo Recepcionista", "monto": 350000},
    {"cat": "Sueldos", "con": "Sueldo Personal Limpieza", "monto": 300000},
    {"cat": "Sueldos", "con": "Cargas Sociales (F.931)", "monto": 200000},
    {"cat": "Sueldos", "con": "Honorarios Contador", "monto": 70000},
    {"cat": "Servicios", "con": "Luz (Edesur/Edenor)", "monto": 150000},
    {"cat": "Servicios", "con": "Agua (AySA)", "monto": 40000},
    {"cat": "Servicios", "con": "Gas (Metrogas) - Vestuarios", "monto": 60000},
    {"cat": "Servicios", "con": "Internet (Fibertel/Telecentro)", "monto": 35000},
    {"cat": "Impuestos", "con": "Monotributo / AFIP", "monto": 50000},
    {"cat": "Impuestos", "con": "Ingresos Brutos (IIBB - AGIP)", "monto": 80000},
    {"cat": "Impuestos", "con": "Tasas Municipales (ABL)", "monto": 30000},
    {"cat": "Insumos", "con": "Artículos de Limpieza", "monto": 45000},
    {"cat": "Marketing", "con": "Pauta en Redes Sociales", "monto": 60000},
    {"cat": "Varios", "con": "Servicio de Alarma/Seguridad", "monto": 25000},
]

# Gastos Recurrentes
GASTOS_TRIMESTRALES = [
    {"cat": "Insumos", "con": "Reposición (Pelotas, Pecheras)", "monto": 100000},
]
GASTOS_SEMESTRALES = [
    {"cat": "Mantenimiento", "con": "Mantenimiento Césped (Cepillado)", "monto": 500000},
]
GASTOS_ANUALES = [
    {"cat": "Impuestos", "con": "Habilitación Anual", "monto": 120000},
]

# Gastos Ocasionales (Se asignarán a un mes al azar)
GASTOS_OCASIONALES = [
    {"cat": "Mantenimiento", "con": "Arreglo Plomería (Vestuario)", "monto": 90000},
    {"cat": "Mantenimiento", "con": "Cambio Reflectores Quemados", "monto": 75000},
    {"cat": "Insumos", "con": "Rotura de Redes", "monto": 50000},
]

def simular_gastos():
    """
    Función principal que genera y guarda los gastos de un año.
    """
    print("Iniciando simulación de gastos para un año...")
    
    # Usamos el año actual (2025) para la simulación
    AÑO_ACTUAL = datetime.now().year 
    
    # --- Contexto de la Aplicación ---
    # Esto es OBLIGATORIO para que SQLAlchemy sepa a qué DB conectarse
    with app.app_context():
        try:
            # --- 1. GASTOS RECURRENTES ---
            print("Cargando gastos fijos y recurrentes...")
            for mes in range(1, 13):
                print(f"  Procesando Mes {mes}/{AÑO_ACTUAL}...")
                
                # Insertar todos los gastos mensuales
                for gasto_data in GASTOS_MENSUALES:
                    # Usamos el día 15 como fecha de pago estándar
                    fecha_gasto_str = f"{AÑO_ACTUAL}-{mes:02d}-15"
                    gasto = Gasto(
                        fecha=fecha_gasto_str,
                        monto=gasto_data['monto'],
                        categoria=gasto_data['cat'],
                        concepto=gasto_data['con'],
                        descripcion="Gasto mensual simulado"
                    )
                    db.session.add(gasto)
                
                # Insertar gastos trimestrales
                if mes in [3, 6, 9, 12]:
                    for gasto_data in GASTOS_TRIMESTRALES:
                        fecha_gasto_str = f"{AÑO_ACTUAL}-{mes:02d}-10"
                        gasto = Gasto(fecha=fecha_gasto_str, monto=gasto_data['monto'], categoria=gasto_data['cat'], concepto=gasto_data['con'], descripcion="Gasto trimestral simulado")
                        db.session.add(gasto)

                # Insertar gastos semestrales
                if mes in [6, 12]:
                    for gasto_data in GASTOS_SEMESTRALES:
                        fecha_gasto_str = f"{AÑO_ACTUAL}-{mes:02d}-20"
                        gasto = Gasto(fecha=fecha_gasto_str, monto=gasto_data['monto'], categoria=gasto_data['cat'], concepto=gasto_data['con'], descripcion="Gasto semestral simulado")
                        db.session.add(gasto)

                # Insertar gastos anuales
                if mes == 1:
                    for gasto_data in GASTOS_ANUALES:
                        fecha_gasto_str = f"{AÑO_ACTUAL}-{mes:02d}-25"
                        gasto = Gasto(fecha=fecha_gasto_str, monto=gasto_data['monto'], categoria=gasto_data['cat'], concepto=gasto_data['con'], descripcion="Gasto anual simulado")
                        db.session.add(gasto)
            
            # --- 2. GASTOS OCASIONALES ---
            print("\nCargando gastos ocasionales (en meses aleatorios)...")
            for gasto_data in GASTOS_OCASIONALES:
                mes_aleatorio = random.randint(1, 12)
                dia_aleatorio = random.randint(1, 28) # Usamos 28 para evitar problemas con Febrero
                fecha_gasto_str = f"{AÑO_ACTUAL}-{mes_aleatorio:02d}-{dia_aleatorio:02d}"
                
                gasto = Gasto(
                    fecha=fecha_gasto_str,
                    monto=gasto_data['monto'],
                    categoria=gasto_data['cat'],
                    concepto=gasto_data['con'],
                    descripcion="Gasto ocasional simulado"
                )
                db.session.add(gasto)
                print(f"  -> '{gasto_data['con']}' asignado al {fecha_gasto_str}")

            # --- 3. COMMIT A LA BASE DE DATOS ---
            print("\nGuardando todos los gastos en la base de datos...")
            db.session.commit()
            print("\n¡Éxito! La simulación de gastos ha sido guardada en la base de datos.")

        except Exception as e:
            print(f"\n*** ERROR: Ocurrió un problema y no se pudieron guardar los gastos. ***")
            print(f"Detalle del error: {e}")
            print("Haciendo rollback (revirtiendo cambios)...")
            db.session.rollback()
        finally:
            print("Simulación terminada.")

# --- Punto de entrada para ejecutar el script ---
if __name__ == "__main__":
    simular_gastos()