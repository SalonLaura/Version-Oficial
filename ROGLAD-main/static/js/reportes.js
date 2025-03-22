document.addEventListener('DOMContentLoaded', function() {
    // Gráfico de ventas
    const ctx = document.getElementById('salesChart').getContext('2d');
    const chartData = JSON.parse(document.getElementById('chartData').textContent);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Ventas por día',
                data: chartData.data,
                borderColor: '#3498db',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Historial de Ventas'
                }
            }
        }
    });
    
    // Botón de impresión
    document.getElementById('printReport').addEventListener('click', function() {
        window.print();
    });
});