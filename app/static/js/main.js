// Main JavaScript for AutoLT v2

// Bootstrap tooltips initialization
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Search functionality
function setupSearch(searchInputId, tableBodyId) {
    const searchInput = document.getElementById(searchInputId);
    const tableBody = document.getElementById(tableBodyId);
    
    if (!searchInput || !tableBody) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = tableBody.getElementsByTagName('tr');
        
        Array.from(rows).forEach(function(row) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

// AJAX form submission helper
function submitAjaxForm(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (successCallback) successCallback(data);
                showAlert('Операция выполнена успешно', 'success');
            } else {
                if (errorCallback) errorCallback(data);
                showAlert('Произошла ошибка: ' + (data.message || 'Неизвестная ошибка'), 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (errorCallback) errorCallback(error);
            showAlert('Произошла ошибка при выполнении запроса', 'danger');
        });
    });
}

// Show alert helper
function showAlert(message, type) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const mainContainer = document.querySelector('main.container');
    if (mainContainer) {
        mainContainer.insertBefore(alertContainer, mainContainer.firstChild);
    }
}

// Confirm deletion helper
function confirmDelete(message, callback) {
    if (confirm(message || 'Вы уверены, что хотите удалить этот элемент?')) {
        callback();
    }
}

// Format date helper
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Update job status dynamically
function updateJobStatus(jobId) {
    fetch(`/jobs/api/jobs/${jobId}`)
        .then(response => response.json())
        .then(data => {
            const statusElement = document.getElementById(`job-status-${jobId}`);
            if (statusElement) {
                statusElement.textContent = data.last_build_status || 'Unknown';
            }
        })
        .catch(error => console.error('Error updating job status:', error));
}