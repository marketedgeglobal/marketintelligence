# {{ title }}

**Report Date:** {{ date }}

## Overview

This automated weekly report tracks emerging funding opportunities across **{{ countries|join(', ') }}**. The report highlights grants, tenders, subsidies, and development programs across key sectors:

{% for sector in sectors %}
- {{ sector }}
{% endfor %}

**Total Opportunities:** {{ total_count }}

---

## Opportunities by Country

{% for country in countries %}
### {{ country }}

{% set country_opportunities = by_country[country] %}
{% if country_opportunities %}
{% for opp in country_opportunities %}
#### {{ opp.title }}

- **Type:** {{ opp.opportunity_type }}
- **Sector:** {{ opp.sector }}
- **Description:** {{ opp.description }}
{% if opp.amount %}
- **Funding Amount:** {{ opp.amount }}
{% endif %}
{% if opp.deadline %}
- **Deadline:** {{ opp.deadline.strftime('%Y-%m-%d') }}
{% endif %}
{% if opp.source %}
- **Source:** {{ opp.source }}
{% endif %}
{% if opp.url %}
- **URL:** [Link]({{ opp.url }})
{% endif %}

---

{% endfor %}
{% else %}
*No opportunities currently tracked for this country.*

---

{% endif %}
{% endfor %}

## Opportunities by Sector

{% for sector in sectors %}
### {{ sector }}

{% set sector_opportunities = by_sector[sector] %}
{% if sector_opportunities %}
{% for opp in sector_opportunities %}
- **{{ opp.title }}** ({{ opp.country }}) - {{ opp.opportunity_type }}
{% endfor %}
{% else %}
*No opportunities currently tracked for this sector.*
{% endif %}

{% endfor %}

---

## About This Report

This report is automatically generated weekly to help identify emerging market opportunities in key agricultural and environmental sectors across Bolivia, Bangladesh, and Myanmar. The information is compiled from various sources including:

- International development agencies
- Government funding programs
- NGO and foundation grants
- Commercial tenders and procurement opportunities

For more information or to contribute opportunities, please visit the repository.

---

*Report generated on {{ date }}*
