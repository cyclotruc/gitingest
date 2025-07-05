function waitForStars() {
    return new Promise((resolve) => {
        const check = () => {
            const stars = document.getElementById('github-stars');

            if (stars && stars.textContent !== '0') {resolve();}
            else {setTimeout(check, 10);}
        };

        check();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('input_text');
    const form = document.getElementById('ingestForm');

    if (urlInput && urlInput.value.trim() && form) {
    // Wait for stars to be loaded before submitting
        waitForStars().then(() => {
            const submitEvent = new SubmitEvent('submit', {
                cancelable: true,
                bubbles: true
            });

            Object.defineProperty(submitEvent, 'target', {
                value: form,
                enumerable: true
            });
            handleSubmit(submitEvent, true);
        });
    }
});
