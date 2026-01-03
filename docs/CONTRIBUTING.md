# Contributing to CarScout Pipeline

Looking to contribute to CarScout Pipeline? All contributions from the community are welcome to help improve the project.

## How to Contribute

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/carscout_pipe.git
   cd carscout_pipe
   ```
3. **Set up the environment**:
   ```bash
   uv sync
   cp .env.example .env
   ```
4. **Create a branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/my-new-feature
   ```
5. **Make your changes** and commit them:
   ```bash
   git commit -m "feat: add amazing new feature"
   ```
6. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```
7. **Submit a Pull Request** to the main repository.

## Development Guidelines

- **Code Style**: We use `ruff` for linting and formatting. Please run `ruff check .` before committing.
- **Testing**: Ensure all tests pass. Run `pytest` to verify.
- **Commits**: Please follow [Conventional Commits](https://www.conventionalcommits.org/).

## Reporting Issues

If you find a bug or have a feature request, please open an issue on the GitHub repository.
