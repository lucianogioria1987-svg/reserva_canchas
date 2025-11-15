import os
import random

# --- IMPORTANTE: Importamos la app, la DB y el modelo Usuario ---
# Esto permite que este script se conecte a tu base de datos
from app import app, db, Usuario

def crear_usuarios_automaticos(num_usuarios=150):
    """
    Crea 150 usuarios automáticos en la base de datos MySQL 
    si la tabla de usuarios está vacía.
    """
    print(f"Iniciando la creación de {num_usuarios} usuarios...")

    # --- 1. VERIFICAMOS LA BASE DE DATOS (NO EL JSON) ---
    if Usuario.query.count() > 0:
        print(f"La tabla 'usuarios' ya tiene datos ({Usuario.query.count()} usuarios). No se agregarán nuevos.")
        return

    print(f"La tabla 'usuarios' está vacía. Generando {num_usuarios} usuarios...")

    # Listas de nombres y apellidos (de tu script original)
    nombres = ["Juan", "María", "Carlos", "Ana", "Luis", "Laura", "Pedro", "Sofía", "José", "Elena",
               "Miguel", "Isabel", "Javier", "Carmen", "Francisco", "Lucía", "Daniel", "Paula", "Jorge", "Martina",
               "Alejandro", "Sara", "Manuel", "Claudia", "Ricardo", "Andrea", "Fernando", "Julia", "Pablo", "Valeria",
               "Raúl", "Adriana", "Sergio", "Patricia", "Andrés", "Raquel", "Roberto", "Natalia", "Eduardo", "Verónica",
               "Diego", "Olga", "Gabriel", "Diana", "Héctor", "Camila", "Joaquín", "Teresa", "Víctor", "Rosa"]
    
    apellidos = ["García", "Rodríguez", "González", "Fernández", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
                 "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Álvarez", "Romero", "Alonso", "Gutiérrez", "Navarro",
                 "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez", "Serrano", "Blanco", "Molina", "Morales",
                 "Suárez", "Ortega", "Delgado", "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias", "Medina",
                 "Garrido", "Cortes", "Castillo", "Santos", "Lozano", "Guerrero", "Cano", "Prieto", "Méndez", "Cruz"]

    dnis_existentes = set()
    nombres_usuario_existentes = set()
    
    nuevos_usuarios_db = []
    usuarios_creados = 0
    
    while usuarios_creados < num_usuarios:
        # Generar datos aleatorios
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        
        # Generar DNI único de 8 dígitos
        while True:
            dni = str(random.randint(10000000, 99999999))
            if dni not in dnis_existentes:
                dnis_existentes.add(dni)
                break
        
        # Generar nombre de usuario único (como en tu script original)
        base_usuario = f"usuario{usuarios_creados + 1}"
        nombre_usuario = base_usuario
        
        contador = 1
        while nombre_usuario in nombres_usuario_existentes:
            nombre_usuario = f"{base_usuario}_{contador}"
            contador += 1
        
        nombres_usuario_existentes.add(nombre_usuario)
        
        # --- 2. CREAR EL OBJETO DE BASE DE DATOS ---
        # (El 'id' se asigna automáticamente por la DB)
        nuevo_usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            dni=dni,
            nombre_usuario=nombre_usuario
        )
        
        # --- 3. ASIGNAR Y HASHEAR LA CONTRASEÑA ---
        # (Usa la función set_password que definimos en el modelo)
        nuevo_usuario.set_password("Contraseña1!")
        
        nuevos_usuarios_db.append(nuevo_usuario)
        usuarios_creados += 1
        
        print(f"Usuario {usuarios_creados}: {nombre_usuario} - {nombre} {apellido} - DNI: {dni}")

    # --- 4. GUARDAR TODO EN LA BASE DE DATOS ---
    try:
        db.session.add_all(nuevos_usuarios_db)
        db.session.commit()
        print(f"¡Proceso completado! Se han creado y guardado {usuarios_creados} usuarios en la base de datos.")
        print("Todos los usuarios tienen la contraseña: Contraseña1!")
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar usuarios en la base de datos: {e}")

if __name__ == '__main__':
    # --- 5. ENVOLVER EN EL CONTEXTO DE LA APP ---
    # (Necesario para que el script pueda hablar con la DB)
    with app.app_context():
        crear_usuarios_automaticos(150)