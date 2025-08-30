import os
import json
import random

# Definir la ruta del archivo de usuarios
CARPETA_DATOS = os.path.join(os.path.dirname(__file__), 'datos')
USUARIOS_NORMAL_FILE = os.path.join(CARPETA_DATOS, 'usuarios.json')

def cargar_datos_json(filepath):
    """Carga datos desde un archivo JSON. Si no existe o está vacío, retorna una lista vacía."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error al cargar {filepath}: {e}")
        return []

def guardar_datos_json(filepath, data):
    """Guarda datos en un archivo JSON."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Datos guardados exitosamente en {filepath}.")
    except Exception as e:
        print(f"Error al guardar {filepath}: {e}")

def crear_usuarios_automaticos(num_usuarios=100):
    """Crea un número específico de usuarios de forma automática y los guarda en el archivo JSON."""
    print(f"Iniciando la creación de {num_usuarios} usuarios automáticos...")

    # Listas de nombres y apellidos para generar datos realistas
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

    # Cargar los usuarios existentes para no sobrescribirlos
    usuarios = cargar_datos_json(USUARIOS_NORMAL_FILE)
    
    # Obtener el ID más alto actual para evitar duplicados
    max_id = 0
    if usuarios:
        try:
            # Buscar el ID más alto entre los usuarios existentes
            for user in usuarios:
                if isinstance(user, dict) and 'id' in user:
                    user_id = user['id']
                    if isinstance(user_id, int) and user_id > max_id:
                        max_id = user_id
        except (ValueError, TypeError):
            print("Error al procesar IDs existentes. Se reiniciará la numeración.")
            max_id = 0

    # Obtener DNIs existentes para evitar duplicados
    dnis_existentes = set()
    nombres_usuario_existentes = set()
    
    for usuario in usuarios:
        if isinstance(usuario, dict):
            if 'dni' in usuario:
                dnis_existentes.add(usuario['dni'])
            if 'nombre_usuario' in usuario:
                nombres_usuario_existentes.add(usuario['nombre_usuario'])

    nuevos_usuarios = []
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
        
        # Generar nombre de usuario único
        base_usuario = f"usuario{max_id + usuarios_creados + 1}"
        nombre_usuario = base_usuario
        
        # Verificar que el nombre de usuario no exista (aunque es poco probable con este formato)
        contador = 1
        while nombre_usuario in nombres_usuario_existentes:
            nombre_usuario = f"{base_usuario}_{contador}"
            contador += 1
        
        nombres_usuario_existentes.add(nombre_usuario)
        
        # Usar la contraseña fija "Contraseña1!" para todos los usuarios
        contrasena = "Contraseña1!"
        
        # Crear el usuario con todos los campos requeridos
        nuevo_usuario = {
            "id": max_id + usuarios_creados + 1,
            "nombre": nombre,
            "apellido": apellido,
            "dni": dni,
            "nombre_usuario": nombre_usuario,
            "contrasena": contrasena
        }
        
        nuevos_usuarios.append(nuevo_usuario)
        usuarios_creados += 1
        
        print(f"Usuario {max_id + usuarios_creados}: {nombre_usuario} - {nombre} {apellido} - DNI: {dni}")

    # Combinar la lista existente con los nuevos usuarios
    usuarios.extend(nuevos_usuarios)
    
    # Guardar la lista completa de usuarios
    guardar_datos_json(USUARIOS_NORMAL_FILE, usuarios)
    print(f"¡Proceso completado! Se han creado y guardado {usuarios_creados} usuarios.")
    print("Todos los usuarios tienen la contraseña: Contraseña1!")

if __name__ == '__main__':
    crear_usuarios_automaticos(100)