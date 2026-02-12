"""
Market Intelligence Opportunity Data Model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Opportunity:
    """Represents a funding opportunity"""
    
    title: str
    country: str
    sector: str
    opportunity_type: str
    description: str
    amount: Optional[str] = None
    deadline: Optional[datetime] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate the opportunity data"""
        valid_countries = ["Bolivia", "Bangladesh", "Myanmar"]
        valid_sectors = [
            "Agribusiness",
            "Ranching and livestock",
            "Fisheries and aquaculture",
            "Climate and environment"
        ]
        valid_types = ["Grants", "Tenders", "Subsidies", "Development programs"]
        
        if self.country not in valid_countries:
            raise ValueError(f"Country must be one of {valid_countries}")
        if self.sector not in valid_sectors:
            raise ValueError(f"Sector must be one of {valid_sectors}")
        if self.opportunity_type not in valid_types:
            raise ValueError(f"Opportunity type must be one of {valid_types}")


@dataclass
class Report:
    """Represents a complete market intelligence report"""
    
    title: str
    report_date: datetime
    opportunities: List[Opportunity]
    countries: List[str]
    sectors: List[str]
    
    def get_opportunities_by_country(self, country: str) -> List[Opportunity]:
        """Filter opportunities by country"""
        return [opp for opp in self.opportunities if opp.country == country]
    
    def get_opportunities_by_sector(self, sector: str) -> List[Opportunity]:
        """Filter opportunities by sector"""
        return [opp for opp in self.opportunities if opp.sector == sector]
    
    def get_opportunities_by_type(self, opp_type: str) -> List[Opportunity]:
        """Filter opportunities by type"""
        return [opp for opp in self.opportunities if opp.opportunity_type == opp_type]
