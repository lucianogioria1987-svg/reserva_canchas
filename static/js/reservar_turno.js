document.addEventListener('DOMContentLoaded', () => {
    // --- 1. Inicialización de variables y elementos del DOM ---
    const calendarGrid = document.getElementById('calendarGrid');
    const currentMonthYearEl = document.getElementById('currentMonthYear');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const selectedDateText = document.getElementById('selectedDateText');
    const availableSlots = document.getElementById('availableSlots');
    const reservationForm = document.getElementById('reservationForm');
    const messageBox = document.getElementById('messageBox');
    
    // Elementos del formulario oculto
    const formFecha = document.getElementById('form-fecha');
    const formCancha = document.getElementById('form-cancha');
    const formHoraInicio = document.getElementById('form-hora_inicio');
    const formHoraFin = document.getElementById('form-hora_fin');
    const selectedCanchaName = document.getElementById('selectedCanchaName');
    const selectedTimeRange = document.getElementById('selectedTimeRange');
    const formCanchaInfo = document.getElementById('form-cancha-info');
    
    let today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();
    let selectedDate = null;
    let turnosDisponiblesData = {}; // Para almacenar los datos de la API

    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

    // --- 2. Funciones de ayuda ---
    function getFormattedDate(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function hideMessageBox() {
        messageBox.classList.add('hidden');
        messageBox.textContent = '';
    }
    
    function showMessageBox(message, type = 'error') {
        messageBox.classList.remove('hidden', 'bg-red-100', 'text-red-800', 'bg-green-100', 'text-green-800');
        if (type === 'error') {
            messageBox.classList.add('bg-red-100', 'text-red-800');
        } else if (type === 'success') {
            messageBox.classList.add('bg-green-100', 'text-green-800');
        }
        messageBox.textContent = message;
    }

    // --- 3. Renderizado del calendario ---
    function renderCalendar() {
        calendarGrid.innerHTML = '';
        currentMonthYearEl.textContent = `${months[currentMonth]} ${currentYear}`;
        
        const firstDay = new Date(currentYear, currentMonth, 1);
        const lastDay = new Date(currentYear, currentMonth + 1, 0);
        const startDayOfWeek = firstDay.getDay();

        // Rellenar días vacíos al principio
        for (let i = 0; i < startDayOfWeek; i++) {
            const emptyCell = document.createElement('div');
            calendarGrid.appendChild(emptyCell);
        }

        // Rellenar los días del mes
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(currentYear, currentMonth, day);
            const dateStr = getFormattedDate(date);
            const dayCell = document.createElement('div');
            dayCell.textContent = day;
            dayCell.classList.add(
                'day-cell', 
                'p-2', 'rounded-full', 'text-center', 'cursor-pointer', 
                'hover:bg-gray-200', 'transition', 'duration-200'
            );

            // Deshabilitar días anteriores a hoy
            if (date < new Date(today.getFullYear(), today.getMonth(), today.getDate())) {
                dayCell.classList.add('opacity-50', 'cursor-not-allowed', 'text-gray-400');
                dayCell.onclick = null;
            } else {
                dayCell.onclick = () => handleDateClick(dateStr, dayCell);
                if (dateStr === getFormattedDate(today)) {
                    dayCell.classList.add('today');
                }
                if (dateStr === selectedDate) {
                    dayCell.classList.add('selected');
                }
            }
            calendarGrid.appendChild(dayCell);
        }
    }

    // --- 4. Manejo de eventos de la interfaz ---
    function handleDateClick(dateStr, element) {
        // Remover la clase 'selected' de la celda anterior
        const prevSelected = document.querySelector('.day-cell.selected');
        if (prevSelected) {
            prevSelected.classList.remove('selected');
        }

        // Agregar la clase 'selected' a la celda actual
        element.classList.add('selected');
        selectedDate = dateStr;
        selectedDateText.textContent = dateStr;
        
        reservationForm.classList.add('hidden'); // Ocultar el formulario
        hideMessageBox();
        fetchAvailableSlots(dateStr);
    }
    
    function handleSlotClick(canchaId, horaInicio, horaFin, cancha) {
        // Deseleccionar los turnos previamente seleccionados
        document.querySelectorAll('.slot-button.selected').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        // Seleccionar el turno actual
        const btn = document.querySelector(`button[data-cancha-id='${canchaId}'][data-hora-inicio='${horaInicio}']`);
        if (btn) btn.classList.add('selected');
        
        // Rellenar el formulario oculto
        formFecha.value = selectedDate;
        formCancha.value = canchaId;
        formHoraInicio.value = horaInicio;
        formHoraFin.value = horaFin;
        
        // Rellenar los detalles de confirmación
        selectedCanchaName.textContent = cancha.nombre;
        selectedTimeRange.textContent = `${horaInicio} a ${horaFin}`;
        formCanchaInfo.innerHTML = `
            <strong>Nombre:</strong> ${cancha.nombre} <br>
            <strong>Tipo:</strong> ${cancha.tipo} <br>
            <strong>Condición:</strong> ${cancha.condicion} <br>
            <strong>Monto Total (1h):</strong> $${cancha.monto * 1}
        `;
        
        reservationForm.classList.remove('hidden'); // Mostrar el formulario
    }

    // --- 5. Interacción con la API de Flask ---
    async function fetchAvailableSlots(date) {
        availableSlots.innerHTML = '<p class="text-center text-gray-500">Cargando turnos...</p>';
        try {
            const response = await fetch(`/api/turnos_disponibles/${date}`);
            const data = await response.json();
            
            if (response.ok) {
                turnosDisponiblesData = data;
                renderAvailableSlots(data);
            } else {
                showMessageBox(data.error || 'Error al cargar los turnos.');
            }
        } catch (error) {
            console.error('Error fetching slots:', error);
            showMessageBox('Error de conexión. Inténtalo de nuevo más tarde.');
        }
    }

    function renderAvailableSlots(data) {
    availableSlots.innerHTML = '';
    const { canchas, horarios_disponibles } = data;
    
    if (!canchas || canchas.length === 0) {
        availableSlots.innerHTML = '<p class="text-center text-gray-500">No hay canchas disponibles.</p>';
        return;
    }

    // Generar todas las horas posibles (de 14:00 a 23:00)
    const allHours = [];
    for (let h = 14; h < 23; h++) {
        allHours.push(`${h.toString().padStart(2, '0')}:00`);
    }

    let tableHTML = `
        <table class="w-full text-left table-auto border-collapse">
            <thead>
                <tr class="bg-gray-200 text-gray-700">
                    <th class="p-3 border border-gray-300 w-[15%]">Horario</th>
                    ${canchas.map(cancha => 
                        `<th class="p-3 border border-gray-300 text-center w-[17%]">
                            <span class="font-bold">${cancha.nombre}</span><br>
                            <span class="text-xs font-normal">Tamaño: ${cancha.tipo}</span><br>
                            <span class="text-xs font-normal">Condición: ${cancha.condicion}</span><br>
                            <span class="text-sm font-semibold text-indigo-600">Valor: $${cancha.monto}</span>
                        </th>`
                    ).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    allHours.forEach(horaInicio => {
        const horaFin = new Date(new Date('2000/01/01 ' + horaInicio).getTime() + 60 * 60000).toTimeString().slice(0, 5);
        
        tableHTML += `
            <tr>
                <td class="p-3 border border-gray-300 font-semibold">${horaInicio} - ${horaFin}</td>
                ${canchas.map(cancha => {
                    // Verificar si este horario está disponible para esta cancha
                    const disponible = horarios_disponibles[cancha.id]?.some(
                        slot => slot.hora_inicio === horaInicio
                    );
                    
                    const buttonClass = disponible 
                        ? 'slot-button bg-green-100 text-green-800 hover:bg-green-200 cursor-pointer' 
                        : 'slot-button disabled bg-gray-300 text-gray-500 cursor-not-allowed';
                    
                    return `
                        <td class="p-1 border border-gray-300 text-center">
                            <button 
                                type="button" 
                                class="w-full py-2 px-1 text-xs sm:text-sm font-semibold rounded-lg transition duration-200 ${buttonClass}"
                                data-cancha-id="${cancha.id}"
                                data-hora-inicio="${horaInicio}"
                                data-hora-fin="${horaFin}"
                                ${!disponible ? 'disabled' : ''}
                            >
                                ${disponible ? 'Disponible' : 'Ocupado'}
                            </button>
                        </td>
                    `;
                }).join('')}
            </tr>
        `;
    });

    tableHTML += `</tbody></table>`;
    availableSlots.innerHTML = tableHTML;

    // Asignar eventos a los botones
    document.querySelectorAll('.slot-button:not(.disabled)').forEach(button => {
        button.addEventListener('click', (e) => {
            const canchaId = e.target.getAttribute('data-cancha-id');
            const horaInicio = e.target.getAttribute('data-hora-inicio');
            const horaFin = e.target.getAttribute('data-hora-fin');
            const cancha = canchas.find(c => c.id == canchaId);
            handleSlotClick(canchaId, horaInicio, horaFin, cancha);
        });
    });
}

    // --- 6. Inicialización y Event Listeners ---
    prevMonthBtn.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar();
    });

    nextMonthBtn.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar();
    });

    renderCalendar();
});

