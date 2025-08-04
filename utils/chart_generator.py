import os
import re
import logging
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date
from models.schemas import StructuredCompanyDoc

logger = logging.getLogger(__name__)

# Set matplotlib style for professional charts
plt.style.use('default')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

def extract_market_numbers(text: str) -> Dict[str, float]:
    """Extract market size numbers from text"""
    market_data = {}
    
    # Patterns for market size extraction
    patterns = [
        r'TAM[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|trillion|M|B|T)',
        r'SAM[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|trillion|M|B|T)',
        r'SOM[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|trillion|M|B|T)',
        r'Total Addressable Market[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|trillion|M|B|T)',
        r'Serviceable Addressable Market[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|trillion|M|B|T)',
        r'Serviceable Obtainable Market[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|trillion|M|B|T)',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for value, unit in matches:
            try:
                num_value = float(value)
                # Convert to billions for consistency
                if unit.lower() in ['million', 'm']:
                    num_value /= 1000
                elif unit.lower() in ['trillion', 't']:
                    num_value *= 1000
                
                if 'tam' in pattern.lower() or 'total addressable market' in pattern.lower():
                    market_data['TAM'] = num_value
                elif 'sam' in pattern.lower() or 'serviceable addressable market' in pattern.lower():
                    market_data['SAM'] = num_value
                elif 'som' in pattern.lower() or 'serviceable obtainable market' in pattern.lower():
                    market_data['SOM'] = num_value
                    
            except ValueError:
                continue
    
    return market_data

def extract_funding_data(bullets: List[str]) -> List[Dict[str, any]]:
    """Extract funding data from bullets"""
    funding_data = []
    
    # Patterns for funding extraction
    patterns = [
        r'(\d{4})[:\s]*\$?(\d+(?:\.\d+)?)\s*(million|billion|M|B)\s*(Series\s+[A-Z]|Seed|Pre-seed|IPO)',
        r'Raised\s+\$?(\d+(?:\.\d+)?)\s*(million|billion|M|B)\s*(Series\s+[A-Z]|Seed|Pre-seed|IPO)\s*in\s*(\d{4})',
        r'(\d{4})[:\s]*(\d+(?:\.\d+)?)\s*(million|billion|M|B)\s*funding',
    ]
    
    for bullet in bullets:
        bullet_lower = bullet.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, bullet_lower, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) == 4:  # Year, Amount, Unit, Round
                        year = int(match[0])
                        amount = float(match[1])
                        unit = match[2]
                        round_type = match[3]
                    elif len(match) == 3:  # Amount, Unit, Round, Year
                        amount = float(match[0])
                        unit = match[1]
                        round_type = match[2]
                        # Try to extract year from the bullet
                        year_match = re.search(r'(\d{4})', bullet)
                        year = int(year_match.group(1)) if year_match else datetime.now().year
                    else:
                        continue
                    
                    # Convert to millions for consistency
                    if unit.lower() in ['billion', 'b']:
                        amount *= 1000
                    
                    funding_data.append({
                        'year': year,
                        'amount': amount,
                        'round': round_type,
                        'description': bullet
                    })
                    
                except (ValueError, IndexError):
                    continue
    
    return funding_data

def extract_traction_data(metrics: Dict[str, str], bullets: List[str]) -> List[Dict[str, any]]:
    """Extract traction data from metrics and bullets"""
    traction_data = []
    
    # Extract from metrics
    for metric, value in metrics.items():
        # Look for year and number in the value
        year_match = re.search(r'(\d{4})', value)
        number_match = re.search(r'(\d+(?:\.\d+)?)', value)
        
        if year_match and number_match:
            try:
                year = int(year_match.group(1))
                number = float(number_match.group(1))
                
                # Determine if it's users, revenue, etc.
                metric_type = metric.lower()
                if 'user' in metric_type or 'mau' in metric_type:
                    metric_type = 'Users'
                elif 'revenue' in metric_type or 'sales' in metric_type:
                    metric_type = 'Revenue'
                else:
                    metric_type = metric
                
                traction_data.append({
                    'year': year,
                    'value': number,
                    'metric': metric_type,
                    'source': value
                })
            except ValueError:
                continue
    
    # Extract from bullets
    for bullet in bullets:
        # Look for patterns like "1M users in 2021", "5M MAU in 2023"
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(M|K|million|thousand)\s*(users?|MAU|DAU)\s*in\s*(\d{4})',
            r'(\d+(?:\.\d+)?)\s*(M|K|million|thousand)\s*in\s*(\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, bullet, re.IGNORECASE)
            for match in matches:
                try:
                    number = float(match[0])
                    unit = match[1]
                    metric_type = match[2] if len(match) > 3 else 'Unknown'
                    year = int(match[-1])
                    
                    # Convert to consistent units
                    if unit.lower() in ['k', 'thousand']:
                        number /= 1000
                    
                    traction_data.append({
                        'year': year,
                        'value': number,
                        'metric': metric_type,
                        'source': bullet
                    })
                except (ValueError, IndexError):
                    continue
    
    return traction_data

def create_market_chart(market_data: Dict[str, float], output_path: str) -> bool:
    """Create market size pie chart"""
    if not market_data or len(market_data) < 2:
        return False
    
    try:
        labels = list(market_data.keys())
        sizes = list(market_data.values())
        
        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        
        # Format labels with values
        for i, label in enumerate(labels):
            value = sizes[i]
            if value >= 1000:
                formatted_value = f"${value/1000:.1f}T"
            else:
                formatted_value = f"${value:.1f}B"
            labels[i] = f"{label}\n({formatted_value})"
        
        ax.set_title('Market Opportunity Breakdown', fontsize=14, fontweight='bold', pad=20)
        
        # Save chart
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Market chart saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create market chart: {e}")
        return False

def create_funding_chart(funding_data: List[Dict[str, any]], output_path: str) -> bool:
    """Create funding timeline chart"""
    if not funding_data:
        return False
    
    try:
        # Sort by year
        funding_data.sort(key=lambda x: x['year'])
        
        years = [item['year'] for item in funding_data]
        amounts = [item['amount'] for item in funding_data]
        rounds = [item['round'] for item in funding_data]
        
        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(years, amounts, color='#2E86AB', alpha=0.7)
        
        # Add value labels on bars
        for i, (bar, amount) in enumerate(zip(bars, amounts)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.01,
                   f'${amount:.0f}M\n{rounds[i]}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Year', fontweight='bold')
        ax.set_ylabel('Funding Amount ($M)', fontweight='bold')
        ax.set_title('Funding History', fontsize=14, fontweight='bold', pad=20)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}M'))
        
        # Rotate x-axis labels if needed
        if len(years) > 5:
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Funding chart saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create funding chart: {e}")
        return False

def create_traction_chart(traction_data: List[Dict[str, any]], output_path: str) -> bool:
    """Create traction growth chart"""
    if not traction_data:
        return False
    
    try:
        # Group by metric type
        metrics = {}
        for item in traction_data:
            metric_type = item['metric']
            if metric_type not in metrics:
                metrics[metric_type] = []
            metrics[metric_type].append(item)
        
        # Create line chart
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
        for i, (metric_type, data) in enumerate(metrics.items()):
            # Sort by year
            data.sort(key=lambda x: x['year'])
            years = [item['year'] for item in data]
            values = [item['value'] for item in data]
            
            color = colors[i % len(colors)]
            ax.plot(years, values, marker='o', linewidth=2, markersize=8, 
                   label=metric_type, color=color)
        
        ax.set_xlabel('Year', fontweight='bold')
        ax.set_ylabel('Value (Millions)', fontweight='bold')
        ax.set_title('Traction Growth', fontsize=14, fontweight='bold', pad=20)
        
        # Add legend
        if len(metrics) > 1:
            ax.legend()
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}M'))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Traction chart saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create traction chart: {e}")
        return False

def generate_charts(structured_doc: StructuredCompanyDoc, output_dir: str) -> Dict[str, str]:
    """
    Generate visual charts from structured memo data.
    
    Args:
        structured_doc: StructuredCompanyDoc object with memo data
        output_dir: Directory to save chart images
        
    Returns:
        Dictionary mapping chart types to file paths
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    chart_paths = {}
    
    # Generate market chart
    if structured_doc.market and structured_doc.market.has_content():
        market_text = structured_doc.market.text or ""
        market_bullets = structured_doc.market.bullets or []
        
        # Combine text and bullets for market data extraction
        market_content = market_text + " " + " ".join(market_bullets)
        market_data = extract_market_numbers(market_content)
        
        if market_data and len(market_data) >= 2:
            market_path = os.path.join(output_dir, "market_chart.png")
            if create_market_chart(market_data, market_path):
                chart_paths["market"] = market_path
    
    # Generate funding chart
    if structured_doc.funding and structured_doc.funding.has_content():
        funding_bullets = structured_doc.funding.bullets or []
        funding_data = extract_funding_data(funding_bullets)
        
        if funding_data:
            funding_path = os.path.join(output_dir, "funding_chart.png")
            if create_funding_chart(funding_data, funding_path):
                chart_paths["funding"] = funding_path
    
    # Generate traction chart
    if structured_doc.traction and structured_doc.traction.has_content():
        traction_metrics = structured_doc.traction.metrics or {}
        traction_bullets = structured_doc.traction.bullets or []
        traction_data = extract_traction_data(traction_metrics, traction_bullets)
        
        if traction_data:
            traction_path = os.path.join(output_dir, "traction_chart.png")
            if create_traction_chart(traction_data, traction_path):
                chart_paths["traction"] = traction_path
    
    logger.info(f"Generated {len(chart_paths)} charts: {list(chart_paths.keys())}")
    return chart_paths

def generate_charts_for_memo(company_name: str, structured_doc: StructuredCompanyDoc) -> Dict[str, str]:
    """
    Convenience function to generate charts for a company memo.
    
    Args:
        company_name: Name of the company
        structured_doc: StructuredCompanyDoc object
        
    Returns:
        Dictionary mapping chart types to file paths
    """
    output_dir = f"data/memos/{company_name.replace(' ', '_')}_charts"
    return generate_charts(structured_doc, output_dir) 