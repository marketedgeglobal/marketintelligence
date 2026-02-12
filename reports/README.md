# Reports Directory

This directory contains the automatically generated Market Intelligence Opportunity Reports.

## Reports

Reports are generated weekly (every Monday at 9:00 AM UTC) and are named using the format:
- `report_YYYYMMDD.md`

Example: `report_20260212.md`

## Manual Generation

To manually generate a report:

```bash
cd src
python report_generator.py ../data/sample_opportunities.json
```

## Report Format

Each report includes:
1. **Overview**: Summary of the report scope and total opportunities
2. **Opportunities by Country**: Detailed listings organized by Bolivia, Bangladesh, and Myanmar
3. **Opportunities by Sector**: Summary view organized by the four key sectors
4. **About This Report**: Information about sources and how to contribute

## Latest Report

The most recent report can always be found by checking the latest dated file in this directory.
