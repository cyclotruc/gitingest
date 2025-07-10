// Fetch GitHub stars
function formatStarCount(count) {
    if (count >= 1000) {return `${ (count / 1000).toFixed(1) }k`;}

    return count.toString();
}

async function fetchGitHubStars() {
    try {
        const res = await fetch('https://api.github.com/repos/coderamp-labs/gitingest');

        if (!res.ok) {throw new Error(`${res.status} ${res.statusText}`);}
        const data = await res.json();

        document.getElementById('github-stars').textContent =
        formatStarCount(data.stargazers_count);
    } catch (err) {
        console.error('Error fetching GitHub stars:', err);
        const el = document.getElementById('github-stars').parentElement;

        if (el) {el.style.display = 'none';}
    }
}

// auto-run when script loads
fetchGitHubStars();
