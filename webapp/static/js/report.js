document.addEventListener('DOMContentLoaded', function() {
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
