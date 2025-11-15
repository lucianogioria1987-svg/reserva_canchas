# ⚽ Sistema de Reservas de Canchas

Este proyecto es una aplicación web integral para la gestión de reservas de canchas deportivas , construida con Flask y SQLAlchemy (MySQL). La aplicación soporta dos roles de usuario (Clientes y Administradores) con paneles y funcionalidades diferenciadas.

El sistema va más allá de un simple CRUD y ofrece un módulo de inteligencia de negocio (BI) para el administrador, con informes estadísticos y financieros.

📋 Características del Panel de Usuario (Cliente)
Autenticación Completa: Registro de nuevos usuarios (con validación de DNI y usuario único), inicio de sesión y cierre de sesión.

Panel de Usuario: Un panel principal que muestra al usuario un resumen de sus próximos turnos activos .

Sistema de Reservas Dinámico:

Formulario de reserva que consume una API interna ( /api/turnos_disponibles/<fecha>) para mostrar la disponibilidad en tiempo real.

La API valida en el servidor los horarios ocupados para evitar colisiones (doble reserva).

Gestión de Turnos:

Historial Completo: Una vista ( /mis_turnos) donde el usuario puede ver todo su historial de reservas (tanto activadas como canceladas).

Autogestión: Permite al usuario cancelar sus propias reservas activas.

🚀 Características del Panel de Administración
El administrador tiene acceso a un panel de gestión y análisis de negocio mucho más potente:

Dashboard de KPIs: Una vista principal con métricas clave (KPIs) en tiempo real:

Ingresos totales del mes en curso.

Total de reservas para el día de hoy.

Conteo total de usuarios y canchas registradas.

Gestión de Canchas (CRUD): Control total para agregar, editar y eliminar canchas. Incluye validación para no eliminar canchas que ya tengan reservas históricas.

Gestión de Usuarios: Visualización de todos los clientes y administradores registrados en la base de datos.

Supervisión de Turnos:

Visualización de todos los turnos activos del sistema, con detalles de qué usuario reservó y en qué cancha.

Historial separado de todos los turnos cancelados .

Permiso para cancelar cualquier turno de cualquier usuario.

Módulo de Inteligencia de Negocios (BI) y Reportes:

Informe Financiero: Desglose detallado de ingresos (reservas activas) agrupados por día, semana, mes, trimestre, semestre y año.

Panel de Estadísticas Avanzadas: Reportes generados dinámicamente sobre:

Top 5 Usuarios (los que más reservan y los que más cancelan).

Ranking de Canchas más populares.

Horarios de Mayor y Menor Demanda (Horas pico).

Días de la Semana con mayor afluencia.

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
