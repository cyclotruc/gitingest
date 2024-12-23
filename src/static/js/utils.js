function copyText(className) {
    const textarea = document.querySelector('.' + className);
    const button = document.querySelector(`button[onclick="copyText('${className}')"]`);
    if (!textarea || !button) return;

    navigator.clipboard.writeText(textarea.value)
        .then(() => {
            const originalContent = button.innerHTML;
            button.innerHTML = 'Copied!';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        })
        .catch(err => {
            const originalContent = button.innerHTML;
            button.innerHTML = 'Failed to copy';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        });
}

function handleSubmit(event, showLoading = false) {
    event.preventDefault();
    const form = event.target || document.getElementById('ingestForm');
    if (!form) return;

    const submitButton = form.querySelector('button[type="submit"]');
    if (!submitButton) return;

    const formData = new FormData(form);

    const slider = document.getElementById('file_size');
    if (slider) {
        formData.delete('max_file_size');
        formData.append('max_file_size', slider.value);
    }

    const patternType = document.getElementById('pattern_type');
    const pattern = document.getElementById('pattern');
    if (patternType && pattern) {
        formData.delete('pattern_type');
        formData.delete('pattern');
        formData.append('pattern_type', patternType.value);
        formData.append('pattern', pattern.value);
    }

    const originalContent = submitButton.innerHTML;
    const currentStars = document.getElementById('github-stars')?.textContent;

    if (showLoading) {
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

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
        .then(response => response.text())
        .then(html => {
            const starCount = currentStars;

            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');

            const existingCanvas = document.getElementById('snow-canvas');
            document.body.innerHTML = newDoc.body.innerHTML;
            if (existingCanvas) {
                document.body.insertBefore(existingCanvas, document.body.firstChild);
            }

            setTimeout(() => {
                initializeSlider();

                const starsElement = document.getElementById('github-stars');
                if (starsElement && starCount) {
                    starsElement.textContent = starCount;
                }

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

function logSliderToSize(position) {
    const minp = 0;
    const maxp = 500;
    const minv = Math.log(1);
    const maxv = Math.log(102400);

    const value = Math.exp(minv + (maxv - minv) * Math.pow(position / maxp, 1.5));
    return Math.round(value);
}

function initializeSlider() {
    const slider = document.getElementById('file_size');
    const sizeValue = document.getElementById('size_value');

    if (!slider || !sizeValue) return;

    function updateSlider() {
        const value = logSliderToSize(slider.value);
        sizeValue.textContent = formatSize(value);
        slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
    }

    slider.addEventListener('input', updateSlider);

    updateSlider();
}

function formatSize(sizeInKB) {
    if (sizeInKB >= 1024) {
        return Math.round(sizeInKB / 1024) + 'mb';
    }
    return Math.round(sizeInKB) + 'kb';
}

document.addEventListener('DOMContentLoaded', initializeSlider);

window.copyText = copyText;
window.handleSubmit = handleSubmit;
window.initializeSlider = initializeSlider;
window.formatSize = formatSize;

function setupGlobalEnterHandler() {
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.target.matches('textarea')) {
            const form = document.getElementById('ingestForm');
            if (form) {
                handleSubmit(new Event('submit'), true);
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeSlider();
    setupGlobalEnterHandler();
});

function toggleSuggestion(suggestion) {
    const patternInput = document.getElementById('pattern');
    if (!patternInput) return;

    const patterns = patternInput.value.split(',').map(p => p.trim());
    const index = patterns.indexOf(suggestion);

    if (index === -1) {
        patterns.push(suggestion);
    } else {
        patterns.splice(index, 1);
    }

    patternInput.value = patterns.filter(p => p).join(', ');
}

function displaySuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('suggestions-container');
    if (!suggestionsContainer) return;

    suggestionsContainer.innerHTML = '';

    suggestions.forEach(suggestion => {
        const suggestionElement = document.createElement('button');
        suggestionElement.textContent = suggestion;
        suggestionElement.classList.add('suggestion-button');
        suggestionElement.addEventListener('click', () => toggleSuggestion(suggestion));
        suggestionsContainer.appendChild(suggestionElement);
    });
}
