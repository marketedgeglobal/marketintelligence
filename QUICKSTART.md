# Quick Start Guide

This guide will help you get started with the Market Intelligence Opportunity Report system.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/marketedgeglobal/marketintelligence.git
   cd marketintelligence
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Generating Your First Report

### Using Sample Data

Generate a report with the provided sample data:

```bash
cd src
python report_generator.py ../data/sample_opportunities.json
```

The report will be created in the `reports/` directory with a filename like `report_20260212.md`.

### Viewing the Report

```bash
# View the most recent report
ls -lt reports/
cat reports/report_*.md | head -50
```

## Adding Custom Opportunities

1. **Create a new JSON file** (e.g., `data/my_opportunities.json`):

```json
{
  "opportunities": [
    {
      "title": "Your Opportunity Title",
      "country": "Bolivia",
      "sector": "Agribusiness",
      "opportunity_type": "Grants",
      "description": "Description of the opportunity",
      "amount": "$1,000,000",
      "deadline": "2026-12-31T00:00:00",
      "source": "Funding Organization",
      "url": "https://example.org/opportunity"
    }
  ]
}
```

2. **Generate the report:**

```bash
cd src
python report_generator.py ../data/my_opportunities.json
```

## Understanding the Report Structure

The generated report includes:

### 1. Overview Section
- Report date
- List of target countries
- List of monitored sectors
- Total opportunity count

### 2. Opportunities by Country
- Detailed information for each opportunity
- Grouped by Bolivia, Bangladesh, and Myanmar
- Includes funding amounts, deadlines, and sources

### 3. Opportunities by Sector
- Summary view of opportunities
- Organized by the four key sectors
- Shows country and opportunity type

## Automation

The repository includes a GitHub Actions workflow that:
- Runs every Monday at 9:00 AM UTC
- Automatically generates a new report
- Commits and pushes the report to the repository

You can also manually trigger the workflow from the GitHub Actions tab.

## Configuration

Modify `config.yaml` to customize:
- Target countries
- Monitored sectors
- Opportunity types
- Report settings

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Explore the `src/` directory to understand the code structure
- Review sample data in `data/sample_opportunities.json`

## Troubleshooting

### Import Errors
If you see import errors, make sure you're running the script from the `src/` directory:
```bash
cd src
python report_generator.py ../data/sample_opportunities.json
```

### Missing Dependencies
If you get module not found errors, reinstall dependencies:
```bash
pip install -r requirements.txt
```

## Getting Help

If you need help:
1. Check the documentation in the repository
2. Review existing issues on GitHub
3. Open a new issue with details about your problem

## What's Next?

- Add real opportunity data from various sources
- Customize the report template
- Set up data collection pipelines
- Integrate with external APIs
- Add email notifications

Happy reporting!
