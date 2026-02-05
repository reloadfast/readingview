# Contributing to Shelf

Thank you for considering contributing to Shelf! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/shelf.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test thoroughly
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/shelf.git
cd shelf

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Audiobookshelf credentials

# Run the application
streamlit run app.py
```

## Code Standards

### Python Style
- Follow PEP 8 style guide
- Use type hints where appropriate
- Include docstrings for functions and classes
- Keep functions focused and single-purpose

### Project Structure
```
shelf/
├── app.py                 # Main application
├── config.py             # Configuration management
├── api/                  # API clients
│   └── audiobookshelf.py
├── components/           # UI components
│   ├── library.py
│   └── statistics.py
└── utils/               # Utility functions
    └── helpers.py
```

### Naming Conventions
- Files: lowercase with underscores (e.g., `library_view.py`)
- Classes: PascalCase (e.g., `AudiobookshelfAPI`)
- Functions: lowercase with underscores (e.g., `get_user_stats`)
- Constants: UPPERCASE (e.g., `DEFAULT_CACHE_TTL`)

## Testing

Before submitting a PR:
- Test with a real Audiobookshelf instance
- Verify all features work as expected
- Check for console errors
- Test with different data scenarios (empty library, many books, etc.)

## Pull Request Guidelines

### PR Title
Use clear, descriptive titles:
- `feat: Add reading goals feature`
- `fix: Correct progress calculation for multi-file books`
- `docs: Update installation instructions`
- `refactor: Simplify statistics calculation`

### PR Description
Include:
- What changes were made
- Why the changes were necessary
- How to test the changes
- Screenshots for UI changes
- Any breaking changes

### Code Review
- Be open to feedback
- Respond to comments promptly
- Make requested changes in new commits
- Squash commits before merge if requested

## Feature Requests

Have an idea? Open an issue with:
- Clear description of the feature
- Use case / motivation
- Proposed implementation (if applicable)
- Mockups or examples (if relevant)

## Bug Reports

When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Relevant logs or error messages
- Screenshots if applicable

## Architecture Principles

When contributing, keep these principles in mind:

### Modularity
- Keep components independent
- Use clear interfaces between modules
- Avoid tight coupling

### Extensibility
- Design for future data sources
- Support future multi-user scenarios
- Keep data models flexible

### Simplicity
- Prefer simple solutions
- Don't over-engineer
- Keep dependencies minimal

### Privacy & Security
- Never commit credentials
- Use environment variables for config
- Validate and sanitize inputs

## Adding New Features

### New Data Sources
If adding support for a new data source:
1. Create a new API client in `api/`
2. Follow the pattern established by `audiobookshelf.py`
3. Implement consistent data models
4. Update configuration to support the new source
5. Document setup and usage

### New Visualizations
If adding new statistics or visualizations:
1. Add to `components/statistics.py` or create a new component
2. Use consistent styling with existing UI
3. Ensure mobile responsiveness
4. Add appropriate loading states
5. Handle empty/error states gracefully

### Database Integration
If adding database support:
1. Keep it optional (direct API access should still work)
2. Use environment variables for configuration
3. Provide migration scripts
4. Document setup clearly
5. Ensure local development remains simple

## Questions?

Feel free to:
- Open an issue for discussion
- Join the community chat (if available)
- Reach out to maintainers

## License

By contributing to Shelf, you agree that your contributions will be licensed under the MIT License.
