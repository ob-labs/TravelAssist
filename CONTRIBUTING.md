# Contributing to TravelAssist

Thank you for your interest in contributing to TravelAssist! We welcome contributions from the community and are grateful for your support.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Questions](#questions)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your contribution
5. Make your changes
6. Test your changes thoroughly
7. Submit a pull request

## How to Contribute

There are many ways to contribute to TravelAssist:

- **Report bugs**: If you find a bug, please create an issue with details
- **Suggest enhancements**: Have an idea? Open an issue to discuss it
- **Improve documentation**: Help us improve our docs
- **Submit code**: Fix bugs or implement new features
- **Review pull requests**: Help review others' contributions

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/ob-labs/TravelAssist.git
   cd TravelAssist
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run tests to ensure everything is working:
   ```bash
   pytest tests/
   ```

## Pull Request Process

1. **Create a branch**: Create a new branch for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**: Implement your changes following our coding standards

3. **Test your changes**: Ensure all tests pass and add new tests if needed
   ```bash
   pytest tests/
   ```

4. **Commit your changes**: Write clear, concise commit messages
   ```bash
   git commit -m "Add feature: description of your changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**: Go to the original repository and create a pull request
   - Provide a clear title and description
   - Reference any related issues
   - Ensure all CI checks pass

7. **Code Review**: Wait for maintainers to review your PR
   - Address any feedback or requested changes
   - Keep your branch up to date with the main branch

8. **Merge**: Once approved, your PR will be merged

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions focused and concise
- Maximum line length: 88 characters (Black formatter default)

### Code Quality

- Write unit tests for new features and bug fixes
- Maintain or improve code coverage
- Use type hints where appropriate
- Keep dependencies up to date

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests where appropriate

## Reporting Bugs

When reporting bugs, please include:

- **Description**: A clear and concise description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: 
  - OS and version
  - Python version
  - Project version
- **Additional Context**: Screenshots, logs, or other relevant information

## Suggesting Enhancements

We welcome enhancement suggestions! When proposing an enhancement:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the proposed enhancement
- **Explain why this enhancement would be useful**
- **List any alternatives** you've considered
- **Include mockups or examples** if applicable

## Questions

If you have questions about contributing:

- Check existing issues and pull requests
- Review the documentation
- Open a new issue with the "question" label

## License

By contributing to TravelAssist, you agree that your contributions will be licensed under the Apache License 2.0.

## Thank You!

Your contributions help make TravelAssist better for everyone. We appreciate your time and effort!
