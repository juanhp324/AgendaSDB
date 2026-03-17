async function cargarEstadisticas() {
    try {
        const res = await fetch('/get_casas');
        const d = await res.json();
        if (d.success) {
            const totalElement = document.getElementById('totalCasas');
            if (totalElement) totalElement.textContent = d.casas.length;
        }
    } catch (err) {
        console.error('Error al cargar estadísticas:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
});
