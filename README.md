# ⚽ Sistema de Reservas de Canchas

Este proyecto es una aplicación web para la gestión de reservas de canchas de fútbol 5.  
Permite a los usuarios registrarse, iniciar sesión, reservar turnos, ver sus reservas y cancelarlas.  
Además, cuenta con un panel de administrador para gestionar usuarios, canchas y visualizar reportes financieros.

---

## 📂 Estructura del proyecto

RESERVA_CANCHAS/
│── datos/                         # Archivos JSON que actúan como base de datos
│   ├── administradores.json
│   ├── canchas.json
│   ├── reservas.json
│   ├── reservas_canceladas.json
│   └── usuarios.json
│
│── plantillas/                    # Vistas HTML para la aplicación (Flask/Jinja)
│   ├── agregar_cancha.html
│   ├── crear_administrador.html
│   ├── crear_usuario.html
│   ├── editar_cancha.html
│   ├── gestionar_canchas.html
│   ├── gestionar_usuarios.html
│   ├── informe_financiero_administrador.html
│   ├── iniciar_sesion_administrador.html
│   ├── iniciar_sesion_usuario.html
│   ├── inicio.html
│   ├── mis_turnos.html
│   ├── panel_administrador.html
│   ├── panel_usuario.html
│   ├── reservar_turno.html
│   ├── ver_turnos_administrador.html
│   └── ver_turnos_cancelados_administrador.html
│
│── static/                        # Recursos estáticos (CSS, JS, imágenes)
│   ├── css/
│   │   └── estilos.css
│   ├── img/
│   │   ├── cancha1.jpg
│   │   ├── cancha2.jpg
│   │   ├── cancha3.jpg
│   │   └── cancha4.jpg
│   └── js/
│       ├── reservar_turno.js
│       └── script.js
│
│── venv/                          # Entorno virtual de Python (ignorado por Git)
│
│── app.py                         # Archivo principal que arranca la aplicación Flask
│── crear_usuarios.py              # Script auxiliar para cargar usuarios
│── simular_reservas.py            # Script para pruebas de reservas
│── .gitignore                     # Archivos y carpetas ignoradas en Git
│── README.md                      # Documentación del proyecto

---

## ⚙️ Requisitos

- Python 3.8 o superior  
- Flask 2.x  
- Dependencias listadas en `requirements.txt`

Instalar dependencias con:
```bash
pip install -r requirements.txt
