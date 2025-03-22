document.addEventListener('DOMContentLoaded', function() {
    // Preview de imagen antes de subir
    document.getElementById('id_imagen').addEventListener('change', function(e) {
        const reader = new FileReader();
        reader.onload = function() {
            document.getElementById('imagePreview').style.backgroundImage = 
                `url(${reader.result})`;
        }
        reader.readAsDataURL(e.target.files[0]);
    });

    // Búsqueda en tiempo real
    document.getElementById('searchInput').addEventListener('input', function(e) {
        const term = e.target.value.toLowerCase();
        document.querySelectorAll('.product-card').forEach(card => {
            const name = card.dataset.name.toLowerCase();
            card.style.display = name.includes(term) ? 'block' : 'none';
        });
    });
});