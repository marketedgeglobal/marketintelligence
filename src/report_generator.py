"""
Report Generator for Market Intelligence
"""
from datetime import datetime
from typing import List
import yaml
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from models import Opportunity, Report


class ReportGenerator:
    """Generates market intelligence reports"""
    
    def __init__(self, config_path: str = None, template_dir: str = None):
        """Initialize the report generator"""
        if config_path is None:
            # Default to config.yaml in the parent directory
            config_path = Path(__file__).parent.parent / "config.yaml"
        if template_dir is None:
            # Default to templates directory in the parent directory
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.config = self._load_config(str(config_path))
        self.template_dir = str(template_dir)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_report(self, opportunities: List[Opportunity]) -> Report:
        """Create a report from a list of opportunities"""
        return Report(
            title=self.config['report']['title'],
            report_date=datetime.now(),
            opportunities=opportunities,
            countries=self.config['countries'],
            sectors=self.config['sectors']
        )
    
    def generate_markdown(self, report: Report, output_path: str = None) -> str:
        """Generate a markdown report"""
        template = self.env.get_template('report_template.md')
        
        # Prepare data for template
        data = {
            'title': report.title,
            'date': report.report_date.strftime('%Y-%m-%d'),
            'countries': report.countries,
            'sectors': report.sectors,
            'opportunities': report.opportunities,
            'total_count': len(report.opportunities)
        }
        
        # Generate opportunities grouped by country
        data['by_country'] = {
            country: report.get_opportunities_by_country(country)
            for country in report.countries
        }
        
        # Generate opportunities grouped by sector
        data['by_sector'] = {
            sector: report.get_opportunities_by_sector(sector)
            for sector in report.sectors
        }
        
        markdown_content = template.render(**data)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(markdown_content)
        
        return markdown_content


def main():
    """Main function to generate report"""
    import sys
    import json
    
    # Load opportunities from JSON file if provided
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        opportunities = []
        for opp_data in data.get('opportunities', []):
            opp = Opportunity(
                title=opp_data['title'],
                country=opp_data['country'],
                sector=opp_data['sector'],
                opportunity_type=opp_data['opportunity_type'],
                description=opp_data['description'],
                amount=opp_data.get('amount'),
                deadline=datetime.fromisoformat(opp_data['deadline']) if opp_data.get('deadline') else None,
                source=opp_data.get('source'),
                url=opp_data.get('url'),
                published_date=datetime.fromisoformat(opp_data['published_date']) if opp_data.get('published_date') else None
            )
            opportunities.append(opp)
    else:
        # Use sample data
        opportunities = []
    
    # Generate report
    generator = ReportGenerator()
    report = generator.create_report(opportunities)
    
    # Ensure output is relative to project root, not src directory
    project_root = Path(__file__).parent.parent
    output_file = project_root / "reports" / f"report_{report.report_date.strftime('%Y%m%d')}.md"
    markdown = generator.generate_markdown(report, str(output_file))
    
    print(f"Report generated: {output_file}")
    print(f"Total opportunities: {len(opportunities)}")


if __name__ == "__main__":
    main()
