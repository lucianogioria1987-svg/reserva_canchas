document.addEventListener('DOMContentLoaded', function() {
    const btnIniciarSesion = document.getElementById('btn-iniciar-sesion');
    const submenuIniciarSesion = document.getElementById('submenu-iniciar-sesion');

    if (btnIniciarSesion && submenuIniciarSesion) {
        btnIniciarSesion.addEventListener('click', function() {
            submenuIniciarSesion.classList.toggle('show');
        });

        // Cerrar el menú si se hace clic fuera
        document.addEventListener('click', function(event) {
            if (!btnIniciarSesion.contains(event.target) && !submenuIniciarSesion.contains(event.target)) {
                if (submenuIniciarSesion.classList.contains('show')) {
                    submenuIniciarSesion.classList.remove('show');
                }
            }
        });
    }

    console.log("Frontend script cargado para Mi Cancha F5.");
});