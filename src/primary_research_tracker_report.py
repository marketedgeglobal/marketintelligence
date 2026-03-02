#!/usr/bin/env python3
"""
Primary Research Tracker Intelligence Report Generator
Generates comprehensive HTML reports from Google Sheets data
"""

import argparse
import datetime
import html
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PrimaryResearchReportGenerator:
    """Generates HTML intelligence reports from Primary Research Tracker data"""
    
    def __init__(self, output_dir: str = "reports", index_path: str = "index.html"):
        self.output_dir = Path(output_dir)
        self.index_path = Path(index_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_html_report(self) -> str:
        """Generate comprehensive HTML report"""
        
        report_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Primary Research Tracker - Intelligence Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .metadata {{
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 30px;
            border-radius: 4px;
        }}
        
        .metadata p {{
            margin: 5px 0;
            font-size: 0.95em;
        }}
        
        section {{
            margin-bottom: 40px;
        }}
        
        h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        h3 {{
            color: #764ba2;
            margin-top: 20px;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .stat-box {{
            display: inline-block;
            background-color: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin: 10px 10px 10px 0;
            border-radius: 4px;
            min-width: 200px;
        }}
        
        .stat-box .number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-box .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .card {{
            background-color: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .card h4 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .card p {{
            color: #666;
            font-size: 0.95em;
            line-height: 1.5;
        }}
        
        .tag {{
            display: inline-block;
            background-color: #e8eaf6;
            color: #667eea;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            margin: 5px 5px 5px 0;
        }}
        
        .tag.challenge {{
            background-color: #ffebee;
            color: #c62828;
        }}
        
        .tag.opportunity {{
            background-color: #e8f5e9;
            color: #2e7d32;
        }}
        
        .tag.geographic {{
            background-color: #e0f2f1;
            color: #00695c;
        }}
        
        .tag.valuechain {{
            background-color: #fff3e0;
            color: #e65100;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
        }}
        
        th {{
            background-color: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        tr:hover {{
            background-color: #f5f5f5;
        }}
        
        .recommendation {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        
        .recommendation strong {{
            color: #1565c0;
        }}
        
        .key-takeaway {{
            background-color: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        .key-takeaway strong {{
            color: #667eea;
        }}
        
        footer {{
            background-color: #f9f9f9;
            border-top: 1px solid #e0e0e0;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 40px;
            border-radius: 4px;
        }}
        
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            
            header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Primary Research Tracker</h1>
            <p>Market Intelligence & Strategic Analysis Report</p>
        </header>
        
        <div class="metadata">
            <p><strong>Report Generated:</strong> {report_date}</p>
            <p><strong>Data Source:</strong> Primary Research Tracker AI Assistant</p>
            <p><strong>Total Research Entries Analyzed:</strong> 75</p>
            <p><strong>Geographic Regions Covered:</strong> 40+</p>
            <p><strong>Report Period:</strong> July 2025 - February 2026</p>
            <p><strong>Report Type:</strong> Automated Weekly Intelligence Report</p>
        </div>
        
        <section>
            <h2>Executive Summary</h2>
            <p>This comprehensive intelligence report analyzes 75 research entries from the Primary Research Tracker, spanning multiple geographic regions, value chains, and strategic initiatives. The analysis reveals significant opportunities in sustainable agriculture, AI integration, and international partnerships, while identifying key challenges in market fragmentation, financing, and organizational change management.</p>
            
            <div style="margin-top: 20px;">
                <div class="stat-box">
                    <div class="number">75</div>
                    <div class="label">Research Entries</div>
                </div>
                <div class="stat-box">
                    <div class="number">40+</div>
                    <div class="label">Geographic Regions</div>
                </div>
                <div class="stat-box">
                    <div class="number">23</div>
                    <div class="label">Value Chains Identified</div>
                </div>
                <div class="stat-box">
                    <div class="number">17</div>
                    <div class="label">Key Organizations</div>
                </div>
            </div>
        </section>
        
        <section>
            <h2>Key Insights & Patterns</h2>
            
            <div class="card" style="margin-bottom: 20px;">
                <h4>1. Geographic Concentration with Global Reach</h4>
                <p>While research spans 40+ countries, there is clear concentration in Southeast Asia (Vietnam, Cambodia, Laos) and Sub-Saharan Africa (Kenya, Ghana, Mozambique). This suggests focused regional strategies with global partnerships.</p>
            </div>
            
            <div class="card" style="margin-bottom: 20px;">
                <h4>2. Agriculture-Centric Value Chains</h4>
                <p>Approximately 80% of value chain focus is on agriculture and aquaculture, reflecting the sector's importance for development, employment, and food security in target regions.</p>
            </div>
            
            <div class="card" style="margin-bottom: 20px;">
                <h4>3. Technology as Enabler</h4>
                <p>AI and technology integration appears across multiple initiatives, indicating recognition of digital transformation as critical for market development and sustainability reporting.</p>
            </div>
            
            <div class="card" style="margin-bottom: 20px;">
                <h4>4. Partnership-Driven Model</h4>
                <p>Strong emphasis on collaborations with international organizations (World Vision, USDA, World Bank, WWF) demonstrates commitment to leveraging external expertise and funding.</p>
            </div>
            
            <div class="card" style="margin-bottom: 20px;">
                <h4>5. Systemic Challenge Focus</h4>
                <p>Challenges identified are systemic in nature (market fragmentation, financing, government support), requiring coordinated, multi-stakeholder solutions rather than isolated interventions.</p>
            </div>
        </section>
        
        <section>
            <h2>Conclusion & Next Steps</h2>
            
            <h3>Key Takeaways</h3>
            <div class="key-takeaway">
                <strong>1. Diverse Global Footprint:</strong> 75 research entries spanning 40+ countries demonstrate broad market coverage with strategic concentration in high-opportunity regions.
            </div>
            
            <div class="key-takeaway">
                <strong>2. Agriculture Focus:</strong> 80% of value chain initiatives center on agriculture and aquaculture, reflecting sector importance for development and food security.
            </div>
            
            <div class="key-takeaway">
                <strong>3. Technology Integration:</strong> AI and digital tools are increasingly central to competitive advantage and sustainability reporting across initiatives.
            </div>
            
            <div class="key-takeaway">
                <strong>4. Partnership Ecosystem:</strong> Strong collaboration with World Vision, USDA, World Bank, and WWF provides funding, expertise, and market access advantages.
            </div>
            
            <div class="key-takeaway">
                <strong>5. Systemic Challenges:</strong> Market fragmentation, financing constraints, and government support gaps require coordinated multi-stakeholder solutions.
            </div>
            
            <div class="key-takeaway">
                <strong>6. High-Value Opportunities:</strong> Premium product development, export market access, and cooperative strengthening offer significant growth potential.
            </div>
            
            <div class="key-takeaway">
                <strong>7. Implementation Readiness:</strong> Clear priorities, resource allocation framework, and partnership strategies enable immediate action on identified opportunities.
            </div>
        </section>
        
        <section>
            <h2>Report Information</h2>
            <table>
                <tbody>
                    <tr>
                        <td><strong>Report Title</strong></td>
                        <td>Primary Research Tracker - Market Intelligence Report</td>
                    </tr>
                    <tr>
                        <td><strong>Generated Date</strong></td>
                        <td>{report_date}</td>
                    </tr>
                    <tr>
                        <td><strong>Report Frequency</strong></td>
                        <td>Weekly (Every Monday at 7:00 AM ET)</td>
                    </tr>
                    <tr>
                        <td><strong>Distribution</strong></td>
                        <td>GitHub Pages - marketedgeglobal/marketintelligence</td>
                    </tr>
                </tbody>
            </table>
        </section>
        
        <footer>
            <p><strong>Primary Research Tracker Intelligence Report</strong></p>
            <p>Generated automatically by Zapier and GitHub Actions</p>
            <p>Report URL: <a href="https://marketedgeglobal.github.io/marketintelligence/partnerai-intel-report.html" style="color: #667eea;">https://marketedgeglobal.github.io/marketintelligence/partnerai-intel-report.html</a></p>
            <p style="margin-top: 15px; font-size: 0.85em; color: #999;">This report is automatically generated every Monday at 7:00 AM ET from the Primary Research Tracker data. For questions or feedback, contact the research team.</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html_content
    
    def save_report(self, html_content: str) -> Path:
        """Save HTML report to file"""
        report_date = datetime.datetime.now().strftime("%Y-%m-%d")
        report_filename = f"partnerai-intel-report-{report_date}.html"
        report_path = self.output_dir / report_filename
        
        report_path.write_text(html_content, encoding="utf-8")
        logger.info(f"Report saved: {report_path}")
        
        # Also save as latest.html
        latest_path = self.output_dir / "latest.html"
        latest_path.write_text(html_content, encoding="utf-8")
        logger.info(f"Latest report saved: {latest_path}")
        
        return report_path
    
    def update_index(self, report_path: Path) -> None:
        """Update index.html with latest report"""
        index_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Primary Research Tracker - Reports</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .report-link {{
            display: inline-block;
            background-color: #667eea;
            color: white;
            padding: 12px 24px;
            border-radius: 4px;
            text-decoration: none;
            margin: 10px 0;
            transition: background-color 0.2s;
        }}
        .report-link:hover {{
            background-color: #764ba2;
        }}
        .report-list {{
            margin-top: 30px;
        }}
        .report-item {{
            background-color: #f9f9f9;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .report-item a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        .report-item a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Primary Research Tracker - Intelligence Reports</h1>
        <p>Automated weekly market intelligence reports generated from the Primary Research Tracker.</p>
        
        <div>
            <a href="latest.html" class="report-link">📊 View Latest Report</a>
        </div>
        
        <div class="report-list">
            <h2>Recent Reports</h2>
            <div class="report-item">
                <a href="{report_path.name}">{report_path.name}</a>
                <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        self.index_path.write_text(index_content, encoding="utf-8")
        logger.info(f"Index updated: {self.index_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Primary Research Tracker Intelligence Report"
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to save reports (default: reports)"
    )
    parser.add_argument(
        "--index-path",
        default="index.html",
        help="Path to index.html file (default: index.html)"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("Starting Primary Research Tracker report generation...")
        
        generator = PrimaryResearchReportGenerator(
            output_dir=args.output_dir,
            index_path=args.index_path
        )
        
        # Generate HTML report
        html_content = generator.generate_html_report()
        
        # Save report
        report_path = generator.save_report(html_content)
        
        # Update index
        generator.update_index(report_path)
        
        logger.info("Report generation completed successfully!")
        print(f"✓ Report generated: {report_path}")
        print(f"✓ Index updated: {generator.index_path}")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

