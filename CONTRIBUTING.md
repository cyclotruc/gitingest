# Contributing to Gitingest

Thanks for your interest in contributing to **Gitingest** 🚀 Our goal is to keep the codebase friendly to first-time contributors.
If you ever get stuck, reach out on [Discord](https://discord.com/invite/zerRaGK9EC).

---

## How to Contribute (non-technical)

- **Create an Issue** – found a bug or have a feature idea?
  [Open an issue](https://github.com/coderamp-labs/gitingest/issues/new).
- **Spread the Word** – tweet, blog, or tell a friend.
- **Use Gitingest** – real-world usage gives the best feedback. File issues or ping us on [Discord](https://discord.com/invite/zerRaGK9EC) with anything you notice.

---

## How to submit a Pull Request

> **Prerequisites**: The project uses **Python 3.9+** and `pre-commit` for development.

1. **Fork** the repository.

2. **Clone** your fork:

   ```bash
   git clone https://github.com/coderamp-labs/gitingest.git
   cd gitingest
   ```

3. **Set up the dev environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   pre-commit install
   ```

4. **Create a branch** for your changes:

   ```bash
   git checkout -b your-branch
   ```

5. **Make your changes** (and add tests when relevant).

6. **Stage** the changes:

   ```bash
   git add .
   ```

7. **Run the backend test suite**:

   ```bash
   pytest
   ```

8. *(Optional)* **Run `pre-commit` on all files** to check hooks without committing:

   ```bash
   pre-commit run --all-files
   ```

9. **Run the local server** to sanity-check:

    ```bash
    cd src
    uvicorn server.main:app
    ```

    Open [http://localhost:8000](http://localhost:8000) to confirm everything works.

10. **Commit** (signed):

    ```bash
    git commit -S -m "Your commit message"
    ```

    If *pre-commit* complains, fix the problems and repeat **5 – 9**.

11. **Push** your branch:

    ```bash
    git push origin your-branch
    ```

12. **Open a pull request** on GitHub with a clear description.

13. **Iterate** on any review feedback—update your branch and repeat **6 – 11** as needed.

*(Optional) Invite a maintainer to your branch for easier collaboration.*

---

## CSS & build artefacts

- **Do not commit `src/static/css/site.css`.** The CI pipeline runs `npm run build:css` during the container/image build, so the artefact is produced automatically.

    *(Optional) Invite project maintainer to your branch for easier collaboration.*

- When developing locally you may run the build yourself (see step 9) so you can preview the styles.

## Dependency Management

When you add a new import from an external package, make sure to add it to both `requirements.txt` and `pyproject.toml` (if applicable). This ensures all environments and CI/CD pipelines have the correct dependencies installed.
