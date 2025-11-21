# Contributing to BioDYM

Thank you for your interest in contributing to BioDYM! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on [GitHub Issues](https://github.com/JScholz-tech/Biodym_JS/issues) with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, BioDYM version)
- Minimal example code if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:
- A clear description of the proposed feature
- Rationale for why this enhancement would be useful
- Possible implementation approach (if you have ideas)

### Pull Requests

1. **Fork the repository** and create your branch from `master`
2. **Make your changes**:
   - Follow the existing code style (PEP 8, enforced by Ruff)
   - Add NumPy-style docstrings to all new functions
   - Update documentation if needed
3. **Add tests** for any new functionality
4. **Run the test suite**: `uv run pytest`
5. **Run code quality checks**: `ruff format . && ruff check .`
6. **Commit your changes** with a clear commit message
7. **Push to your fork** and submit a pull request

### Commit Message Guidelines

Use clear, descriptive commit messages:
```
type(scope): brief description

Longer description if needed.

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

### Code Style

- **Python**: Follow PEP 8 (enforced by Ruff)
- **Docstrings**: NumPy-style for all public functions
- **Type hints**: Use where appropriate
- **Comments**: Explain "why", not "what"

### Testing

- All new code should include tests
- Run `uv run pytest` before submitting
- Aim for >80% code coverage
- Test both happy paths and edge cases

### Documentation

- Update README.md if adding user-facing features
- Add docstrings to all new functions
- Update USER_GUIDE.md for new features
- Keep CHANGELOG.md updated

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Biodym_JS.git
cd Biodym_JS

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run code quality checks
uv run ruff format .
uv run ruff check .
```

## Getting Help

- Check the [USER_GUIDE.md](05_docs/USER_GUIDE.md)
- Read the [TECHNICAL_DEEP_DIVE.md](05_docs/development/TECHNICAL_DEEP_DIVE.md)
- Ask questions in [GitHub Discussions](https://github.com/JScholz-tech/Biodym_JS/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue or start a discussion if you have questions!

---

Thank you for contributing to BioDYM! 🌱
