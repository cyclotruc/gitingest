// Copy functionality
function copyText(className) {
    const textarea = document.querySelector('.' + className);
    const button = document.querySelector(`button[onclick="copyText('${className}')"]`);
    if (!textarea || !button) return;

    // Copy text
    navigator.clipboard.writeText(textarea.value)
        .then(() => {
            // Store original content
            const originalContent = button.innerHTML;

            // Change button content
            button.innerHTML = 'Copied!';

            // Reset after 1 second
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        })
        .catch(err => {
            // Show error in button
            const originalContent = button.innerHTML;
            button.innerHTML = 'Failed to copy';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        });
}

function validateGithubUrl(url) {
    // Add https:// if missing
    if (!url.startsWith('https://')) {
        url = 'https://' + url;
    }
    
    // Check if it's a valid GitHub URL
    const githubPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+/;
    return githubPattern.test(url);
}

function handleSubmit(event, showLoading = false) {
    event.preventDefault();
    const form = event.target || document.getElementById('ingestForm');
    if (!form) return;

    const submitButton = form.querySelector('button[type="submit"]');
    if (!submitButton) return;

    // Create new FormData from the form
    const formData = new FormData(form);

    // Get the slider value and update formData with the converted value
    const slider = document.getElementById('file_size');
    if (slider) {
        formData.delete('max_file_size');
        formData.append('max_file_size', slider.value);
    }

    // Get the input URL
    const formData = new FormData(form);
    const inputUrl = formData.get('input_text');
    
    // Validate URL
    if (!validateGithubUrl(inputUrl)) {
        const errorMessage = document.getElementById('error-message') || (() => {
            const div = document.createElement('div');
            div.id = 'error-message';
            div.className = 'text-red-500 text-sm mt-2';
            form.appendChild(div);
            return div;
        })();
        errorMessage.textContent = 'Please enter a valid GitHub repository URL (e.g., github.com/user/repo)';
        return;
    }

    const originalContent = submitButton.innerHTML;
    const currentStars = document.getElementById('github-stars')?.textContent;

    if (showLoading) {
        // Change button to loading state
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <div class="flex items-center justify-center">
                <svg class="animate-spin h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="ml-2">Processing...</span>
            </div>
        `;
        submitButton.classList.add('bg-[#ffb14d]');
    }

    // Submit the form
    fetch(form.action, {
        method: 'POST',
        body: formData
    })
        .then(response => response.text())
        .then(html => {
            // Store the star count before updating the DOM
            const starCount = currentStars;

            document.documentElement.innerHTML = html;

            // Wait for next tick to ensure DOM is updated
            setTimeout(() => {
                // Reinitialize slider functionality
                initializeSlider();

                const starsElement = document.getElementById('github-stars');
                if (starsElement && starCount) {
                    starsElement.textContent = starCount;
                }

                // Scroll to results if they exist
                const resultsSection = document.querySelector('[data-results]');
                if (resultsSection) {
                    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 0);
        })
        .catch(error => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;
        });
}

function copyFullDigest() {
    const directoryStructure = document.querySelector('.directory-structure').value;
    const filesContent = document.querySelector('.result-text').value;
    const fullDigest = `${directoryStructure}\n\nFiles Content:\n\n${filesContent}`;
    const button = document.querySelector('[onclick="copyFullDigest()"]');
    const originalText = button.innerHTML;

    navigator.clipboard.writeText(fullDigest).then(() => {
        button.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Copied!
        `;

        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Add the logSliderToSize helper function
function logSliderToSize(position) {
    const minp = 0;
    const maxp = 500;
    const minv = Math.log(1);
    const maxv = Math.log(102400);

    const value = Math.exp(minv + (maxv - minv) * Math.pow(position / maxp, 1.5));
    return Math.round(value);
}

// Move slider initialization to a separate function
function initializeSlider() {
    const slider = document.getElementById('file_size');
    const sizeValue = document.getElementById('size_value');

    if (!slider || !sizeValue) return;

    function updateSlider() {
        const value = logSliderToSize(slider.value);
        sizeValue.textContent = formatSize(value);
        slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
    }

    // Update on slider change
    slider.addEventListener('input', updateSlider);

    // Initialize slider position
    updateSlider();
}

// Add helper function for formatting size
function formatSize(sizeInKB) {
    if (sizeInKB >= 1024) {
        return Math.round(sizeInKB / 1024) + 'mb';
    }
    return Math.round(sizeInKB) + 'kb';
}

// Initialize slider on page load
document.addEventListener('DOMContentLoaded', initializeSlider);

// Make sure these are available globally
window.copyText = copyText;

window.handleSubmit = handleSubmit;
window.initializeSlider = initializeSlider;
window.formatSize = formatSize; 
