# Market Intelligence Opportunity Report

This repository contains the automated weekly **Market Intelligence Opportunity Report**, a publication that tracks emerging funding opportunities across **Bolivia, Bangladesh, and Myanmar**. The report highlights grants, tenders, subsidies, and development programs across key sectors:

- Agribusiness  
- Ranching and livestock  
- Fisheries and aquaculture  
- Climate and environment

## Overview

The Market Intelligence Opportunity Report is designed to help organizations and individuals identify funding and development opportunities in key agricultural and environmental sectors across three focus countries. The report is automatically generated on a weekly basis using data from various sources.

## Features

- **Automated Weekly Reports**: Generates reports every Monday at 9:00 AM UTC
- **Multi-Country Coverage**: Tracks opportunities in Bolivia, Bangladesh, and Myanmar
- **Sector-Specific Insights**: Organizes opportunities by key sectors
- **Multiple Opportunity Types**: Covers grants, tenders, subsidies, and development programs
- **Structured Data**: Uses standardized data models for easy processing and analysis

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       └── weekly-report.yml    # GitHub Actions workflow for automation
├── config.yaml                   # Configuration file
├── data/
│   └── sample_opportunities.json # Sample opportunity data
├── reports/                      # Generated reports (auto-created)
├── src/
│   ├── models.py                # Data models
│   └── report_generator.py      # Report generation script
├── templates/
│   └── report_template.md       # Markdown template for reports
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/marketedgeglobal/marketintelligence.git
cd marketintelligence
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage

#### Generate a Report Manually

To generate a report with sample data:

```bash
cd src
python report_generator.py ../data/sample_opportunities.json
```

The report will be generated in the `reports/` directory with a filename like `report_YYYYMMDD.md`.

#### Add New Opportunities

Opportunities should be added to a JSON file following this structure:

```json
{
  "opportunities": [
    {
      "title": "Opportunity Title",
      "country": "Bolivia|Bangladesh|Myanmar",
      "sector": "Agribusiness|Ranching and livestock|Fisheries and aquaculture|Climate and environment",
      "opportunity_type": "Grants|Tenders|Subsidies|Development programs",
      "description": "Description of the opportunity",
      "amount": "Funding amount (optional)",
      "deadline": "2026-12-31T00:00:00 (optional)",
      "source": "Source organization (optional)",
      "url": "https://example.org/opportunity (optional)",
      "published_date": "2026-01-01T00:00:00 (optional)"
    }
  ]
}
```

## Automation

The repository includes a GitHub Actions workflow that automatically:

1. Runs every Monday at 9:00 AM UTC
2. Generates a new report using the latest opportunity data
3. Commits and pushes the report to the repository

The workflow can also be triggered manually from the Actions tab in GitHub.

## Configuration

The `config.yaml` file contains the main configuration:

- **countries**: List of target countries
- **sectors**: Key sectors to monitor
- **opportunity_types**: Types of opportunities to track
- **report**: Report settings (title, frequency, output format)

## Data Models

### Opportunity

Represents a single funding opportunity with the following attributes:

- `title`: Name of the opportunity
- `country`: Target country (Bolivia, Bangladesh, or Myanmar)
- `sector`: Relevant sector
- `opportunity_type`: Type of opportunity (grant, tender, subsidy, or development program)
- `description`: Detailed description
- `amount`: Funding amount (optional)
- `deadline`: Application deadline (optional)
- `source`: Source organization (optional)
- `url`: Link to more information (optional)
- `published_date`: Date the opportunity was published (optional)

### Report

Represents a complete market intelligence report with methods to:

- Filter opportunities by country
- Filter opportunities by sector
- Filter opportunities by type

## Contributing

Contributions are welcome! To contribute new opportunities or improvements:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-opportunities`)
3. Add your opportunities to the appropriate data file
4. Commit your changes (`git commit -m 'Add new opportunities'`)
5. Push to the branch (`git push origin feature/new-opportunities`)
6. Open a Pull Request

## License

This project is open source and available for public use.

## Contact

For questions or suggestions, please open an issue in this repository.

---

**Generated weekly by GitHub Actions** | Last updated: Check the latest report in the `reports/` directory