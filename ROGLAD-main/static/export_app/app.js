// static/export_app/app.js

document.addEventListener('DOMContentLoaded', () => {
    // Element references
    const searchInput = document.getElementById('searchInput');
    const resultsBody = document.getElementById('resultsBody');
    const exportButtons = document.querySelectorAll('.export-btn');
    let currentSearchTerm = '';
    
    // Debounce function para mejorar performance en búsquedas
    const debounce = (func, delay = 300) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    };

    // Cargar resultados con manejo de errores
    const loadResults = async (searchTerm) => {
        try {
            showLoadingState(true);
            
            const response = await fetch(`/api/data/?search=${encodeURIComponent(searchTerm)}`);
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            updateResultsTable(data.results);
            updateExportButtons(data.count > 0);
            
        } catch (error) {
            showErrorMessage(`Error loading data: ${error.message}`);
        } finally {
            showLoadingState(false);
        }
    };

    // Actualizar tabla de resultados
    const updateResultsTable = (results) => {
        resultsBody.innerHTML = '';
        
        if (results.length === 0) {
            resultsBody.innerHTML = `<tr class="no-results">
                <td colspan="3">No records found</td>
            </tr>`;
            return;
        }
        
        results.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${escapeHTML(item.name)}</td>
                <td>${escapeHTML(item.email)}</td>
                <td>${new Date(item.created_at).toLocaleString()}</td>
            `;
            resultsBody.appendChild(row);
        });
    };

    // Manejar exportación de datos
    const handleExport = async (format) => {
        try {
            if (!currentSearchTerm) {
                alert('Please enter a search term before exporting.');
                return;
            }
            
            const response = await fetch(`/export/?search=${encodeURIComponent(currentSearchTerm)}&format=${format}`);
            
            if (!response.ok) throw new Error(`Export failed: ${response.statusText}`);
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `export.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            showErrorMessage(`Export Error: ${error.message}`);
        }
    };

    // Helpers
    const escapeHTML = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };

    const showLoadingState = (isLoading) => {
        const container = document.querySelector('.container');
        container.classList.toggle('loading', isLoading);
    };

    const showErrorMessage = (message) => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        document.body.prepend(errorDiv);
        setTimeout(() => errorDiv.remove(), 5000);
    };

    const updateExportButtons = (enable) => {
        exportButtons.forEach(button => {
            button.disabled = !enable;
            button.title = enable ? '' : 'No data to export';
        });
    };

    // Event Listeners
    searchInput.addEventListener('input', debounce((e) => {
        currentSearchTerm = e.target.value.trim();
        loadResults(currentSearchTerm);
    }));

    exportButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const format = e.target.dataset.format;
            handleExport(format);
        });
    });

    // Initial load
    loadResults(currentSearchTerm);
});