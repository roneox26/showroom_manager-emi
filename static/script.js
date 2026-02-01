// Custom JavaScript for Showroom Manager

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Form validation
(function() {
    'use strict';
    
    // Fetch all forms that need validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over them and prevent submission
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
})();

// Phone number validation (Bangladesh format)
function validatePhone(phoneInput) {
    const phone = phoneInput.value;
    const pattern = /^01[0-9]{9}$/;
    
    if (phone && !pattern.test(phone)) {
        phoneInput.setCustomValidity('সঠিক ফোন নম্বর লিখুন (01XXXXXXXXX)');
    } else {
        phoneInput.setCustomValidity('');
    }
}

// Add phone validation to all phone inputs
document.addEventListener('DOMContentLoaded', function() {
    const phoneInputs = document.querySelectorAll('input[name="customer_phone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validatePhone(this);
        });
    });
});

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'আপনি কি নিশ্চিত যে আপনি এটি মুছে ফেলতে চান?');
}

// Format currency
function formatCurrency(amount) {
    return '৳' + parseFloat(amount).toFixed(2);
}

// Calculate profit margin
function calculateProfitMargin(buyingPrice, sellingPrice) {
    if (buyingPrice > 0) {
        return ((sellingPrice - buyingPrice) / buyingPrice * 100).toFixed(2);
    }
    return 0;
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Search functionality with debounce
document.addEventListener('DOMContentLoaded', function() {
    const searchInputs = document.querySelectorAll('input[name="search"]');
    searchInputs.forEach(function(input) {
        const form = input.closest('form');
        if (form) {
            input.addEventListener('input', debounce(function() {
                // Auto-submit search after 500ms of no typing
                // Uncomment if you want auto-search
                // form.submit();
            }, 500));
        }
    });
});

// Table row click to expand details (optional)
function makeTableRowsClickable(tableSelector, detailsClass) {
    const table = document.querySelector(tableSelector);
    if (table) {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(function(row) {
            row.addEventListener('click', function(e) {
                // Don't trigger if clicking on a button or link
                if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.closest('button') || e.target.closest('a')) {
                    return;
                }
                
                // Toggle details
                const details = this.querySelector(detailsClass);
                if (details) {
                    details.classList.toggle('d-none');
                }
            });
        });
    }
}

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        window.print();
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'alert alert-success position-fixed top-0 end-0 m-3';
        toast.textContent = 'কপি করা হয়েছে!';
        document.body.appendChild(toast);
        
        setTimeout(function() {
            toast.remove();
        }, 2000);
    }).catch(function(err) {
        console.error('Failed to copy:', err);
    });
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        cols.forEach(function(col) {
            csvRow.push(col.textContent.trim());
        });
        csv.push(csvRow.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'export.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Loading spinner
function showLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>লোড হচ্ছে...';
    
    return function hideLoading() {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// AJAX helper function
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Initialize tooltips (Bootstrap 5)
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Initialize popovers (Bootstrap 5)
document.addEventListener('DOMContentLoaded', function() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

console.log('Showroom Manager JavaScript loaded successfully! 🏪');
