document.addEventListener('DOMContentLoaded', function() {
    const cart = [];
    const products = JSON.parse(document.getElementById('productsData').dataset.products);
    
    // Búsqueda de productos
    const searchInput = document.getElementById('productSearch');
    const resultsContainer = document.getElementById('searchResults');
    
    searchInput.addEventListener('input', function(e) {
        const term = e.target.value.toLowerCase();
        const filtered = products.filter(p => p.nombre.toLowerCase().includes(term));
        
        resultsContainer.innerHTML = filtered.map(p => `
            <div class="product-item" data-id="${p.id}">
                ${p.nombre} - $${p.precio} (Stock: ${p.existencia})
            </div>
        `).join('');
    });
    
    // Agregar producto al carrito
    resultsContainer.addEventListener('click', function(e) {
        if(e.target.closest('.product-item')) {
            const productId = e.target.closest('.product-item').dataset.id;
            const product = products.find(p => p.id == productId);
            
            const existing = cart.find(item => item.id == productId);
            if(existing) {
                existing.cantidad++;
            } else {
                cart.push({
                    id: productId,
                    nombre: product.nombre,
                    precio: product.precio,
                    cantidad: 1
                });
            }
            updateCartDisplay();
        }
    });
    
    // Actualizar visualización del carrito
    function updateCartDisplay() {
        const cartContainer = document.getElementById('cartItems');
        const totalElement = document.getElementById('totalAmount');
        
        cartContainer.innerHTML = cart.map(item => `
            <div class="cart-item">
                <span>${item.nombre} x${item.cantidad}</span>
                <span>$${item.precio * item.cantidad}</span>
                <button class="btn btn-sm btn-danger remove-item" data-id="${item.id}">X</button>
            </div>
        `).join('');
        
        const total = cart.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
        totalElement.textContent = `$${total.toFixed(2)}`;
    }
    
    // Eliminar items del carrito
    document.getElementById('cartItems').addEventListener('click', function(e) {
        if(e.target.classList.contains('remove-item')) {
            const productId = e.target.dataset.id;
            const index = cart.findIndex(item => item.id == productId);
            if(index > -1) {
                cart.splice(index, 1);
                updateCartDisplay();
            }
        }
    });
});