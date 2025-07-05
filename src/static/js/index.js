function submitExample(repoName) {
    const input = document.getElementById('input_text');

    if (input) {
        input.value = repoName;
        input.focus();
    }
}

// Make it visible to inline onclick handlers
window.submitExample = submitExample;
