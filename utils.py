import sqlite3
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io

DB_FILE = "data_cache.db"
OFFLINE_DATA_FILE = "offline_data.json"

def init_database():
    """Initialize SQLite database with district_metrics table"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS district_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            households INTEGER,
            person_days INTEGER,
            expenditure REAL,
            avg_wage REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(state, district, year, month)
        )
    ''')
    conn.commit()
    conn.close()

def get_cache_timestamp(state, district):
    """Get the timestamp of the last cache update for a state/district"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT MAX(updated_at) FROM district_metrics 
        WHERE state = ? AND district = ?
    ''', (state, district))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result[0] else None

def is_cache_valid(state, district, ttl_seconds=86400):
    """Check if cache is still valid (within TTL)"""
    timestamp = get_cache_timestamp(state, district)
    if not timestamp:
        return False
    cache_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return (datetime.now() - cache_time).total_seconds() < ttl_seconds

def save_to_cache(state, district, data_list):
    """Save fetched data to SQLite cache"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for record in data_list:
        cursor.execute('''
            INSERT OR REPLACE INTO district_metrics 
            (state, district, year, month, households, person_days, expenditure, avg_wage, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            state,
            district,
            record['year'],
            record['month'],
            record['households'],
            record['person_days'],
            record['expenditure'],
            record['avg_wage'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    conn.close()

def get_from_cache(state, district):
    """Retrieve data from SQLite cache"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT state, district, year, month, households, person_days, expenditure, avg_wage, updated_at
        FROM district_metrics
        WHERE state = ? AND district = ?
        ORDER BY year DESC, month DESC
    ''', conn, params=(state, district))
    conn.close()
    return df

def get_all_states_from_cache():
    """Get list of all states from cache"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT state FROM district_metrics ORDER BY state')
    states = [row[0] for row in cursor.fetchall()]
    conn.close()
    return states

def get_districts_from_cache(state):
    """Get list of all districts for a state from cache"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT district FROM district_metrics WHERE state = ? ORDER BY district', (state,))
    districts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return districts

def fetch_from_api(state, district=None, api_key=None):
    """
    Fetch MGNREGA data from data.gov.in API
    Note: In production, replace with actual API endpoint and resource ID
    """
    try:
        # Placeholder API call - in production, use actual data.gov.in endpoint
        # url = f"https://api.data.gov.in/resource/<RESOURCE_ID>?filters[state_name]={state}&format=json"
        # if api_key:
        #     url += f"&api-key={api_key}"
        # response = requests.get(url, timeout=10)
        # response.raise_for_status()
        # data = response.json()
        
        # For demo purposes, return None to trigger fallback
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def load_offline_data(state, district=None):
    """Load fallback data from offline_data.json"""
    if not os.path.exists(OFFLINE_DATA_FILE):
        return pd.DataFrame()
    
    with open(OFFLINE_DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if district:
        filtered = [
            record for record in data 
            if record['state'] == state and record['district'] == district
        ]
    else:
        filtered = [
            record for record in data 
            if record['state'] == state
        ]
    
    return pd.DataFrame(filtered)

def get_districts_from_offline(state):
    """Get list of all districts for a state from offline_data.json"""
    df = load_offline_data(state)
    if df.empty:
        return []
    return sorted(df['district'].unique().tolist())

def get_state_average(state, year, month):
    """Calculate state average for comparison"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            AVG(households) as avg_households,
            AVG(person_days) as avg_person_days,
            AVG(expenditure) as avg_expenditure,
            AVG(avg_wage) as avg_avg_wage
        FROM district_metrics
        WHERE state = ? AND year = ? AND month = ?
    ''', (state, year, month))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0]:
        return {
            'households': int(result[0]),
            'person_days': int(result[1]),
            'expenditure': round(result[2], 2),
            'avg_wage': round(result[3], 2)
        }
    return None

def format_indian_number(num):
    """Format numbers in Indian numbering system (lakhs, crores)"""
    if num >= 10000000:
        return f"₹{num/10000000:.2f} Cr"
    elif num >= 100000:
        return f"{num/100000:.2f} L"
    else:
        return f"{num:,.0f}"

def get_month_name(month_num):
    """Get month name from number"""
    months = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    return months.get(month_num, "")

def get_translations():
    """Return English to Hindi translations for UI labels"""
    return {
        'title': {
            'en': 'Our Voice, Our Rights – MGNREGA Dashboard 🇮🇳',
            'hi': 'हमारी आवाज, हमारे अधिकार – मनरेगा डैशबोर्ड 🇮🇳'
        },
        'subtitle': {
            'en': 'Understand your district\'s performance under MGNREGA',
            'hi': 'मनरेगा के तहत अपने जिले के प्रदर्शन को समझें'
        },
        'households': {
            'en': 'Households Worked',
            'hi': 'कुल परिवार'
        },
        'expenditure': {
            'en': 'Total Expenditure',
            'hi': 'कुल व्यय'
        },
        'person_days': {
            'en': 'Person-Days Generated',
            'hi': 'कार्य दिवस'
        },
        'avg_wage': {
            'en': 'Average Wage',
            'hi': 'औसत वेतन'
        },
        'select_state': {
            'en': 'Select State',
            'hi': 'राज्य चुनें'
        },
        'select_district': {
            'en': 'Select District',
            'hi': 'जिला चुनें'
        },
        'fetch_data': {
            'en': 'Fetch Data',
            'hi': 'डेटा प्राप्त करें'
        },
        'performance_summary': {
            'en': 'Performance Summary',
            'hi': 'प्रदर्शन सारांश'
        },
        'read_summary': {
            'en': 'Read Summary',
            'hi': 'सारांश सुनें'
        }
    }

def generate_summary(district, state, latest_data, language='en'):
    """Generate performance summary text in English or Hindi"""
    if latest_data.empty:
        return "No data available" if language == 'en' else "कोई डेटा उपलब्ध नहीं है"
    
    row = latest_data.iloc[0]
    month_name = get_month_name(row['month'])
    households = f"{row['households']:,}"
    person_days = format_indian_number(row['person_days'])
    expenditure = format_indian_number(row['expenditure'])
    
    if language == 'en':
        summary = f"In {month_name} {row['year']}, {households} households in {district} district worked under MGNREGA, "
        summary += f"generating {person_days} person-days and ₹{expenditure} expenditure. "
        summary += f"The average wage was ₹{row['avg_wage']:.2f} per day."
        
        if len(latest_data) > 1:
            prev_row = latest_data.iloc[1]
            change = ((row['person_days'] - prev_row['person_days']) / prev_row['person_days']) * 100
            if change > 0:
                summary += f" This is a {change:.1f}% increase from the previous month."
            elif change < 0:
                summary += f" This is a {abs(change):.1f}% decrease from the previous month."
    else:
        summary = f"{month_name} {row['year']} में, {district} जिले में {households} परिवारों ने मनरेगा के तहत काम किया, "
        summary += f"जिससे {person_days} कार्य दिवस और ₹{expenditure} खर्च हुए। "
        summary += f"औसत वेतन ₹{row['avg_wage']:.2f} प्रति दिन था।"
    
    return summary

def generate_pdf_report(district, state, df, language='en'):
    """Generate a PDF report with metrics and charts"""
    if df.empty:
        return None
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    if language == 'en':
        title_text = f"MGNREGA Performance Report<br/>{district}, {state}"
        subtitle_text = f"Report Generated: {datetime.now().strftime('%B %d, %Y')}"
    else:
        title_text = f"मनरेगा प्रदर्शन रिपोर्ट<br/>{district}, {state}"
        subtitle_text = f"रिपोर्ट तैयार: {datetime.now().strftime('%d/%m/%Y')}"
    
    story.append(Paragraph(title_text, title_style))
    story.append(Paragraph(subtitle_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    latest_record = df.iloc[0]
    month_name = get_month_name(latest_record['month'])
    
    if language == 'en':
        story.append(Paragraph("Key Metrics Summary", heading_style))
        metrics_data = [
            ['Metric', 'Value'],
            ['Latest Month', f"{month_name} {latest_record['year']}"],
            ['Households Worked', f"{latest_record['households']:,}"],
            ['Person-Days Generated', f"{latest_record['person_days']:,}"],
            ['Total Expenditure', format_indian_number(latest_record['expenditure'])],
            ['Average Wage', f"₹{latest_record['avg_wage']:.2f}"]
        ]
    else:
        story.append(Paragraph("मुख्य मैट्रिक्स सारांश", heading_style))
        metrics_data = [
            ['मैट्रिक', 'मूल्य'],
            ['नवीनतम महीना', f"{month_name} {latest_record['year']}"],
            ['कुल परिवार', f"{latest_record['households']:,}"],
            ['कार्य दिवस', f"{latest_record['person_days']:,}"],
            ['कुल व्यय', format_indian_number(latest_record['expenditure'])],
            ['औसत वेतन', f"₹{latest_record['avg_wage']:.2f}"]
        ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))
    
    if len(df) > 1:
        if language == 'en':
            story.append(Paragraph("Monthly Trend Data", heading_style))
            trend_data = [['Month', 'Year', 'Households', 'Person-Days', 'Expenditure', 'Avg Wage']]
        else:
            story.append(Paragraph("मासिक रुझान डेटा", heading_style))
            trend_data = [['महीना', 'वर्ष', 'परिवार', 'कार्य दिवस', 'व्यय', 'वेतन']]
        
        for _, row in df.head(6).iterrows():
            trend_data.append([
                get_month_name(row['month']),
                str(row['year']),
                f"{row['households']:,}",
                f"{row['person_days']:,}",
                format_indian_number(row['expenditure']),
                f"₹{row['avg_wage']:.2f}"
            ])
        
        trend_table = Table(trend_data, colWidths=[1*inch, 0.7*inch, 1*inch, 1.2*inch, 1.2*inch, 1*inch])
        trend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ca02c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
        ]))
        
        story.append(trend_table)
        story.append(Spacer(1, 0.2*inch))
    
    if language == 'en':
        footer_text = "Data Source: Government of India Open Data Portal (data.gov.in)"
        footer_text += "<br/>This report is generated for informational purposes only."
    else:
        footer_text = "डेटा स्रोत: भारत सरकार ओपन डेटा पोर्टल (data.gov.in)"
        footer_text += "<br/>यह रिपोर्ट केवल सूचनात्मक उद्देश्यों के लिए तैयार की गई है।"
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
