// Strike-through / un-strike file lines when the pattern-type menu flips.
function changePattern() {
    const dirPre = document.getElementById('directory-structure-pre');

    if (!dirPre) {return;}

    const treeLineElements = Array.from(dirPre.querySelectorAll('pre[name="tree-line"]'));

    // Skip the first tree line element
    treeLineElements.slice(2).forEach((element) => {
        element.classList.toggle('line-through');
        element.classList.toggle('text-gray-500');
    });
}

// Show/hide the Personal-Access-Token section when the "Private repository" checkbox is toggled.
function toggleAccessSettings() {
    const container = document.getElementById('accessSettingsContainer');
    const examples = document.getElementById('exampleRepositories');
    const show = document.getElementById('showAccessSettings')?.checked;

    container?.classList.toggle('hidden', !show);
    examples?.classList.toggle('lg:mt-0', show);
}



document.addEventListener('DOMContentLoaded', () => {
    toggleAccessSettings();
    changePattern();
});


// Make them available to existing inline attributes
window.changePattern = changePattern;
window.toggleAccessSettings = toggleAccessSettings;
