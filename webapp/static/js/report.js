<!-- Скрипт для показа/скрытия дополнительных фильтров -->
function showHideAdditionalFilters() {
    const extraFilters = document.getElementById('extraFilters');
    if (extraFilters.style.display === 'none') {
        extraFilters.style.display = 'block';
        this.textContent = 'Скрыть дополнительные фильтры';
    } else {
        extraFilters.style.display = 'none';
        this.textContent = 'Показать дополнительные фильтры';
    }
}

