# MGNREGA Dashboard - Our Voice, Our Rights

## Overview

A bilingual (English/Hindi) Streamlit web application that helps Indian citizens understand MGNREGA (Mahatma Gandhi National Rural Employment Guarantee Act) performance metrics for their districts. The app fetches data from India's open government API (data.gov.in), displays key performance indicators, visualizes trends, and enables district-level comparisons. The application is designed for accessibility, targeting rural citizens who need simplified data interpretation.

**Core Purpose**: Bridge the gap between government open data and citizen understanding by providing an intuitive, visual interface for MGNREGA performance monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Architecture

**Pattern**: Single-page application (SPA) with component-based UI structure
- **Framework**: Streamlit for rapid web UI development with Python backend
- **State Management**: Session state for maintaining user selections and cached data
- **Default Configuration**: Uttar Pradesh as the default state for quick access

**Rationale**: Streamlit was chosen for its simplicity in creating data-driven web applications without requiring separate frontend/backend codebases. This reduces complexity and development time while maintaining functionality.

### Data Layer

**Hybrid Data Strategy**: Online-first with offline fallback
- **Primary Source**: Government API (data.gov.in) for real-time MGNREGA metrics
- **Local Cache**: SQLite database (`data_cache.db`) for performance optimization
- **Fallback Data**: JSON file (`offline_data.json`) for offline access
- **Cache Invalidation**: Timestamp-based caching to ensure data freshness

**Database Schema** (SQLite):
```
district_metrics:
  - id (PRIMARY KEY)
  - state, district (compound unique key)
  - year, month (temporal identifiers)
  - households, person_days, expenditure, avg_wage (metrics)
  - updated_at (timestamp for cache management)
```

**Rationale**: The hybrid approach ensures reliability in areas with poor connectivity while optimizing API usage and load times. SQLite provides lightweight, serverless data persistence without infrastructure overhead.

### Data Processing Pipeline

**Flow**: API Request → Cache Check → Data Transformation → Visualization
1. Check cache validity based on timestamp
2. Fetch from API if cache is stale or missing
3. Transform raw API response to structured format
4. Store in SQLite for future requests
5. Fall back to offline JSON if API fails

**Libraries**:
- `pandas`: Data manipulation and aggregation
- `requests`: HTTP client for API calls
- `json`: Parsing offline/API data

### Visualization Layer

**Components**:
- **Metric Cards**: Large, bilingual display of key statistics with trend indicators (green/red/orange)
- **Time Series Charts**: matplotlib for historical trend visualization
- **Comparison Views**: District-level comparative analysis
- **Report Generation**: ReportLab for PDF export functionality

**Key Metrics Displayed**:
- Households Worked (कुल परिवार)
- Total Expenditure (कुल व्यय)
- Person-Days Generated (कार्य दिवस)
- Average Wage (औसत वेतन)

**Rationale**: Visual metrics with color coding provide immediate understanding for users with varying literacy levels. Bilingual labels ensure accessibility across language barriers.

### Localization Architecture

**Bilingual Support**: English + Hindi throughout the UI
- **Static Translations**: Hardcoded Hindi labels for UI elements
- **Dynamic Content**: Supports Hindi rendering for data labels and descriptions
- **Audio Features**: Text-to-speech capability using `gtts` or `pyttsx3` for accessibility

**Rationale**: Hindi support is critical for reaching the target rural demographic. Audio features address literacy barriers.

### Report Generation System

**Technology**: ReportLab for PDF creation
- **Components**: SimpleDocTemplate, Tables, Charts, Paragraphs
- **Layout**: Letter/A4 format with structured sections
- **Embedded Visualizations**: matplotlib charts converted to images and embedded

**Rationale**: PDF reports provide shareable, printable formats that citizens can use for advocacy or record-keeping without requiring internet access.

## External Dependencies

### Government Data API

**Primary Data Source**: data.gov.in MGNREGA API
- **Endpoint**: District-level monthly metrics
- **Data Format**: JSON
- **Update Frequency**: Monthly
- **Access**: Public API (may require API key)

**Handled Scenarios**:
- API unavailability → fallback to offline data
- Rate limiting → caching strategy
- Data inconsistencies → validation layer

### Python Libraries

**Core Dependencies**:
- `streamlit`: Web application framework
- `pandas`: Data analysis and manipulation
- `requests`: HTTP client for API interactions
- `sqlite3`: Built-in database (no external service)
- `matplotlib`: Chart generation
- `reportlab`: PDF report creation
- `plotly`: Interactive visualizations (alternative to matplotlib)
- `gtts` or `pyttsx3`: Text-to-speech for accessibility

**Optional**:
- `geopy`: Geographic services (location-based features)

### Hosting Platform

**Deployment**: Replit web server
- **Runtime**: Python 3 environment
- **Storage**: Persistent filesystem for SQLite database
- **Port**: Web-accessible HTTP server

### File System Dependencies

**Required Files**:
- `offline_data.json`: Static fallback dataset (committed to repository)
- `data_cache.db`: Runtime-generated SQLite database (not in version control)
- `requirements.txt`: Dependency specifications for deployment

**Data Persistence**: SQLite database and generated charts stored on local filesystem, requiring persistent storage configuration on hosting platform.