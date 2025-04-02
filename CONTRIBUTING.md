# Contributing to Gitingest

Thanks for your interest in contributing to Gitingest! 🚀 Gitingest aims to be friendly for first time contributors, with a simple Python and HTML codebase. We would love your help to make it even better. If you need any help while working with the code, please reach out to us on [Discord](https://discord.com/invite/zerRaGK9EC).

## How to Contribute (non-technical)

- **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub. This will help us track and prioritize your request.
- **Spread the Word**: If you like Gitingest, please share it with your friends, colleagues, and on social media. This will help us grow the community and make Gitingest even better.
- **Use Gitingest**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub or by reaching out to us on [Discord](https://discord.com/invite/zerRaGK9EC).

## How to submit a Pull Request

1. Fork the repository.

2. Clone the forked repository:

   ```bash
   git clone https://github.com/cyclotruc/gitingest.git
   cd gitingest
   ```

3. Set up the development environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   pre-commit install
   ```

4. Create a new branch for your changes:

    ```bash
    git checkout -b your-branch
    ```

5. Make your changes. Make sure to add corresponding tests for your changes.

6. Stage your changes:

    ```bash
    git add .
    ```

7. Run the tests:

   ```bash
   pytest
   ```

8. Run the local web server

   1. Navigate to src folder

        ``` bash
        cd src
        ```

   2. Run the local web server:

      ``` bash
      uvicorn server.main:app
      ```

   3. Open your browser and navigate to `http://localhost:8000` to see the app running.

9. Confirm that everything is working as expected. If you encounter any issues, fix them and repeat steps 6 to 8.

10. Commit your changes:

    ```bash
    git commit -m "Your commit message"
    ```

    If `pre-commit` raises any issues, fix them and repeat steps 6 to 9.

11. Push your changes:

    ```bash
    git push origin your-branch
    ```

12. Open a pull request on GitHub. Make sure to include a detailed description of your changes.

13. Wait for the maintainers to review your pull request. If there are any issues, fix them and repeat steps 6 to 12.

    *(Optional) Invite project maintainer to your branch for easier collaboration.*
