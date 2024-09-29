document.addEventListener('DOMContentLoaded', function () {
    // Инициализация Datepicker для всех элементов с классом .datepicker
    $('.datepicker').datepicker({
        format: 'dd-mm-yyyy', // формат даты
        autoclose: true,
        todayHighlight: true,
        language: 'ru'
    });
});

<!-- Скрипт для показа/скрытия дополнительных фильтров -->
function showHideAdditionalFilters(button) {
    const extraFilters = document.getElementById('extraFilters');
    if (extraFilters.style.display === 'none') {
        extraFilters.style.display = 'block';
        button.textContent = 'Скрыть дополнительные фильтры';
    } else {
        extraFilters.style.display = 'none';
        button.textContent = 'Показать дополнительные фильтры';
    }
}

// JavaScript для обработки "Все" чекбоксов
function toggleSaleType(checkbox) {
    const saleTypeCheckboxes = document.querySelectorAll('input[name="sale_types"]');
    if (checkbox.value === 'all' && checkbox.checked) {
        // Если выбран чекбокс "Все", снимаем отметки с остальных
        saleTypeCheckboxes.forEach(cb => {
            if (cb.value !== 'all') {
                cb.checked = false;
            }
        });
    } else {
        // Снимаем отметку с чекбокса "Все", если любой другой выбран
        const selectAllCheckbox = document.querySelector('input[name="sale_types"][value="all"]');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
    }
}

function toggleEvent(checkbox) {
    const eventCheckboxes = document.querySelectorAll('input[name="events"]');

    if (checkbox.value === 'all' && checkbox.checked) {
        // Если выбран чекбокс "Все", снимаем отметки с остальных
        eventCheckboxes.forEach(cb => {
            if (cb.value !== 'all') {
                cb.checked = false;
            }
        });
    } else {
        // Снимаем отметку с чекбокса "Все", если любой другой выбран
        const selectAllCheckbox = document.querySelector('input[name="events"][value="all"]');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
    }
}

function OnSessionsReportLoaded() {
    const allCheckbox = document.getElementById('event_all');
    const eventCheckboxes = document.querySelectorAll('input[name="event_templates"]');

    // If no individual events are checked, select "all"
    function checkDefault() {
        const anyChecked = Array.from(eventCheckboxes).some(checkbox => checkbox.checked);
        if (!anyChecked) {
            allCheckbox.checked = true;
        }
    }

    // When "all" is checked, uncheck all others
    allCheckbox.addEventListener('change', function () {
        if (allCheckbox.checked) {
            eventCheckboxes.forEach(checkbox => checkbox.checked = false);
        }
    });

    // When any individual event is checked, uncheck "all"
    eventCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (checkbox.checked) {
                allCheckbox.checked = false;
            }
        });
    });

    // Run default check on page load
    checkDefault();
}


function OnTicketsReportLoad () {
    // Проверяем, заданы ли дополнительные фильтры
    const orderNumber = document.querySelector('input[name="order_number"]').value;
    const ticketNumber = document.querySelector('input[name="ticket_number"]').value;
    const eventTemplates = document.querySelector('select[name="event_templates"]').value;

    if (orderNumber || ticketNumber || eventTemplates) {
        document.getElementById('extraFilters').style.display = 'block';  // Показываем блок, если фильтры заданы
        document.getElementById('showHideAdditionalFiltersButton').textContent = 'Скрыть дополнительные фильтры';
    }
}