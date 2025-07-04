// Strike-through / un-strike file lines when the pattern-type menu flips.
function changePattern() {
    const files = document.getElementsByName('tree-line');

    files.forEach((el) => {
        if (el.textContent.includes('Directory structure:')) {return;}
        [
            'line-through',
            'text-gray-500',
            'hover:text-inherit',
            'hover:no-underline',
            'hover:line-through',
            'hover:text-gray-500',
        ].forEach((cls) => el.classList.toggle(cls));
    });
}

// Show/hide the Personal-Access-Token section when the “Private repository” checkbox is toggled.
function toggleAccessSettings() {
    const container = document.getElementById('accessSettingsContainer');
    const examples = document.getElementById('exampleRepositories');
    const show = document.getElementById('showAccessSettings')?.checked;

    container?.classList.toggle('hidden', !show);
    examples?.classList.toggle('lg:mt-0', show);
}



document.addEventListener('DOMContentLoaded', () => {
    document
        .getElementById('pattern_type')
        ?.addEventListener('change', () => changePattern());

    document
        .getElementById('showAccessSettings')
        ?.addEventListener('change', toggleAccessSettings);

    // Initial UI sync
    toggleAccessSettings();
    changePattern();
});


// Make them available to existing inline attributes
window.changePattern = changePattern;
window.toggleAccessSettings = toggleAccessSettings;
