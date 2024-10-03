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


function toggleService(checkbox) {
    const serviceCheckboxes = document.querySelectorAll('input[name="services"]');

    if (checkbox.value === 'service_all' && checkbox.checked) {
        // Если выбран чекбокс "Все", снимаем отметки с остальных
        serviceCheckboxes.forEach(cb => {
            if (cb.value !== 'service_all') {
                cb.checked = false;
            }
        });
    } else {
        // Снимаем отметку с чекбокса "Все", если любой другой выбран
        const selectAllCheckbox = document.querySelector('input[name="services"][value="service_all"]');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
    }
}