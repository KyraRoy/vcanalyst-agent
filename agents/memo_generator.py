from datetime import date, datetime
from jinja2 import Template
from models.schemas import StructuredCompanyDoc

MEMO_TEMPLATE = """
# {{ company.name }} Investment Memo
Prepared on {{ date }}

## Investment Recommendations

{% if company.recommendations.has_content() %}
{{ company.recommendations.text }}

{% if company.recommendations.bullets %}
**Key Decision Points:**
{% for bullet in company.recommendations.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
**Investment Decision: [To be determined based on due diligence]**

**Key Decision Points:**
- Speed assessment pending
- Depth evaluation required
- Taste alignment to be verified
- Influence potential needs validation
{% endif %}

{% if company.recommendations.citations %}
**Sources:** {% for citation in company.recommendations.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

---

## 1. Executive Summary
{% if company.intro.has_content() %}
{{ company.intro.text }}

{% if company.intro.bullets %}
**Key Points:**
{% for bullet in company.intro.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
{{ company.name }} is a [industry] company that [brief description of what they do]. The company addresses [core problem] through [unique solution], serving [target market]. [Funding status if available].
{% endif %}

{% if company.intro.citations %}
**Sources:** {% for citation in company.intro.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 2. Company Overview
{% if company.intro.has_content() %}
{{ company.intro.text }}

{% if company.intro.bullets %}
**Key Milestones:**
{% for bullet in company.intro.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
{{ company.name }} is a [industry] company focused on [core business area]. The company was founded to [mission/vision].
{% endif %}

{% if company.intro.citations %}
**Sources:** {% for citation in company.intro.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 3. Problem
{% if company.problem.has_content() %}
{{ company.problem.text }}

{% if company.problem.bullets %}
**Key Issues:**
{% for bullet in company.problem.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Problem description not provided in pitch deck]
{% endif %}

{% if company.problem.citations %}
**Sources:** {% for citation in company.problem.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 4. Solution
{% if company.solution.has_content() %}
{{ company.solution.text }}

{% if company.solution.bullets %}
**Key Value Propositions:**
{% for bullet in company.solution.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Solution details not provided in pitch deck]
{% endif %}

{% if company.solution.citations %}
**Sources:** {% for citation in company.solution.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 5. Product
{% if company.product.has_content() %}
{{ company.product.text }}

{% if company.product.bullets %}
**Key Features:**
{% for bullet in company.product.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Product details not provided in pitch deck]
{% endif %}

{% if company.product.citations %}
**Sources:** {% for citation in company.product.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 6. Business Model
{% if company.business_model.has_content() %}
{{ company.business_model.text }}

{% if company.business_model.bullets %}
**Revenue Streams:**
{% for bullet in company.business_model.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Business model details not provided in pitch deck]
{% endif %}

{% if company.business_model.citations %}
**Sources:** {% for citation in company.business_model.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 7. Market Size
{% if company.market.has_content() %}
{{ company.market.text }}

{% if company.market.bullets %}
**Market Insights:**
{% for bullet in company.market.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Market size data not provided in pitch deck]
{% endif %}

{% if company.market.citations %}
**Sources:** {% for citation in company.market.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 8. Traction
{% if company.traction.has_content() %}
{{ company.traction.text }}

{% if company.traction.bullets %}
**Key Metrics:**
{% for bullet in company.traction.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Traction data not provided in pitch deck]
{% endif %}

{% if company.traction.citations %}
**Sources:** {% for citation in company.traction.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 9. Growth Strategy
{% if company.growth_strategy.has_content() %}
{{ company.growth_strategy.text }}

{% if company.growth_strategy.bullets %}
**Growth Tactics:**
{% for bullet in company.growth_strategy.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Growth strategy details not provided in pitch deck]
{% endif %}

{% if company.growth_strategy.citations %}
**Sources:** {% for citation in company.growth_strategy.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 10. Team
{% if company.team.has_content() %}
{{ company.team.text }}

{% if company.team.bullets %}
**Key Team Members:**
{% for bullet in company.team.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Team information not provided in pitch deck]
{% endif %}

{% if company.team.citations %}
**Sources:** {% for citation in company.team.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 11. Competition
{% if company.competitors.has_content() %}
{{ company.competitors.text }}

{% if company.competitors.bullets %}
**Key Competitors:**
{% for bullet in company.competitors.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Competitive analysis not provided in pitch deck]
{% endif %}

{% if company.competitors.citations %}
**Sources:** {% for citation in company.competitors.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 12. Financials
{% if company.financials.has_content() %}
{{ company.financials.text }}

{% if company.financials.bullets %}
**Financial Highlights:**
{% for bullet in company.financials.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Financial data not provided in pitch deck]
{% endif %}

{% if company.financials.citations %}
**Sources:** {% for citation in company.financials.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 13. Risks
{% if company.risks.has_content() %}
{{ company.risks.text }}

{% if company.risks.bullets %}
**Key Risk Factors:**
{% for bullet in company.risks.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Risk assessment not provided in pitch deck]
{% endif %}

{% if company.risks.citations %}
**Sources:** {% for citation in company.risks.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 14. Timing
{% if company.timing.has_content() %}
{{ company.timing.text }}

{% if company.timing.bullets %}
**Timing Factors:**
{% for bullet in company.timing.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Timing analysis not provided in pitch deck]
{% endif %}

{% if company.timing.citations %}
**Sources:** {% for citation in company.timing.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}

## 15. Moat
{% if company.moat.has_content() %}
{{ company.moat.text }}

{% if company.moat.bullets %}
**Competitive Advantages:**
{% for bullet in company.moat.bullets %}- {{ bullet }}
{% endfor %}
{% endif %}
{% else %}
[Competitive moat analysis not provided in pitch deck]
{% endif %}

{% if company.moat.citations %}
**Sources:** {% for citation in company.moat.citations %}{% if citation.source_type == "gpt_knowledge" %}GPT Training Data{% else %}{% if citation.source_type != "pitch_deck" %}[{{ citation.source_type }}]({{ citation.url }}){% else %}[Pitch Deck]({{ citation.url }}){% endif %}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}
{% endif %}
"""

def generate_memo(company: StructuredCompanyDoc, memo_date: str = None) -> str:
    """Generate a conditional memo using Jinja2 template"""
    if not memo_date:
        memo_date = date.today().strftime('%b %d, %Y')
    
    template = Template(MEMO_TEMPLATE)
    return template.render(company=company, date=memo_date)