# Contributing to Market Intelligence Opportunity Report

Thank you for your interest in contributing to the Market Intelligence Opportunity Report! This document provides guidelines for contributing new opportunities and improvements to the project.

## How to Contribute

### Adding New Opportunities

1. **Prepare Your Data**: Create or update a JSON file in the `data/` directory with opportunity information
2. **Follow the Schema**: Ensure your opportunities follow the required data structure
3. **Submit a Pull Request**: Create a PR with your changes

### Data Structure

Each opportunity must include:

```json
{
  "title": "Required - Name of the opportunity",
  "country": "Required - Bolivia, Bangladesh, or Myanmar",
  "sector": "Required - Agribusiness, Ranching and livestock, Fisheries and aquaculture, or Climate and environment",
  "opportunity_type": "Required - Grants, Tenders, Subsidies, or Development programs",
  "description": "Required - Detailed description",
  "amount": "Optional - Funding amount as string",
  "deadline": "Optional - ISO 8601 format: 2026-12-31T00:00:00",
  "source": "Optional - Source organization",
  "url": "Optional - Link to more information",
  "published_date": "Optional - ISO 8601 format: 2026-01-01T00:00:00"
}
```

### Validation Rules

- **Country**: Must be one of: Bolivia, Bangladesh, Myanmar
- **Sector**: Must be one of:
  - Agribusiness
  - Ranching and livestock
  - Fisheries and aquaculture
  - Climate and environment
- **Opportunity Type**: Must be one of: Grants, Tenders, Subsidies, Development programs
- **Dates**: Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)

### Example Contribution

Create a file `data/new_opportunities.json`:

```json
{
  "opportunities": [
    {
      "title": "Sustainable Rice Farming Initiative",
      "country": "Bangladesh",
      "sector": "Agribusiness",
      "opportunity_type": "Grants",
      "description": "Support for sustainable rice farming practices in flood-prone regions.",
      "amount": "$1,000,000",
      "deadline": "2026-08-15T00:00:00",
      "source": "World Food Programme",
      "url": "https://example.org/grants/bangladesh-rice-2026",
      "published_date": "2026-02-15T00:00:00"
    }
  ]
}
```

Then generate a report to test:

```bash
cd src
python report_generator.py ../data/new_opportunities.json
```

### Code Contributions

If you want to improve the code:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test your changes**: Ensure the report generator still works
5. **Commit your changes**: Use clear, descriptive commit messages
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request**

### Reporting Issues

If you find a bug or have a suggestion:

1. Check if the issue already exists
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (Python version, OS, etc.)

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to classes and functions
- Keep functions focused and concise

## Questions?

If you have questions about contributing, please open an issue with the "question" label.

## License

By contributing, you agree that your contributions will be made available under the same terms as the project.
