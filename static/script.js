// MkweliAML - Basic utilities
console.log('MkweliAML utilities loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM ready - MkweliAML initialized');
    
    // Simple file input feedback
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.files.length > 0) {
                console.log('File selected:', this.files[0].name);
            }
        });
    });
});
