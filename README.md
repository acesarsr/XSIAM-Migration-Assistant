# XSIAM Migration Assistant

A web-based tool to facilitate the migration of detection rules from Splunk and QRadar to Cortex XSIAM, with intelligent coverage analysis against 1,100+ built-in XSIAM analytics.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.124+-green.svg)

## 🌟 Features

### Rule Migration
- **Multi-Platform Support**: Import detection rules from Splunk (JSON) and QRadar (XML)
- **Automatic Conversion**: Heuristic SPL-to-XQL conversion engine
- **Interactive Editor**: Side-by-side comparison and manual editing of converted queries
- **Status Tracking**: Visual indicators for translation progress (Pending/Translated/Reviewed)

### Coverage Analysis ✨
- **1,177 XSIAM Analytics**: Pre-loaded database from Palo Alto Networks documentation
- **Smart Matching**: Intelligent comparison using:
  - Name similarity algorithms
  - MITRE ATT&CK technique mapping
  - Detector tag correlation
- **Confidence Scoring**: Percentage-based match confidence
- **Top 5 Recommendations**: Shows best matching XSIAM analytics with severity levels

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/acesarsr/XSIAM-Migration-Assistant.git
   cd XSIAM-Migration-Assistant
   ```

2. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

4. **Access the application**:
   Open your browser and navigate to [http://localhost:8000](http://localhost:8000)

## 📖 Usage

### Step 1: Upload Rules
1. Select your source platform (Splunk or QRadar)
2. Click "Select File" and choose your exported rules:
   - **Splunk**: JSON format (example: `sample_splunk.json`)
   - **QRadar**: XML format

### Step 2: Review Conversions
- View auto-converted XQL queries in the dashboard
- Status indicators:
  - 🔵 **Translated**: Successfully converted
  - 🟢 **Reviewed**: Manually verified/edited
  - 🟠 **Pending**: Needs attention

### Step 3: Check Coverage
- Click the **"Coverage"** button for any rule
- View matching XSIAM analytics with:
  - Match confidence percentage
  - Severity levels
  - MITRE ATT&CK mappings
  - Detector tags

### Step 4: Edit & Refine
- Click **"Edit"** to manually adjust XQL queries
- Save changes to mark as "Reviewed"

## 🏗️ Architecture

```
xsiam-migration-tool/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── models.py                  # Pydantic data models
│   ├── coverage_analyzer.py       # Coverage matching engine
│   ├── converter/
│   │   └── spl_to_xql.py         # SPL to XQL converter
│   ├── parsers/
│   │   ├── splunk_parser.py      # Splunk JSON parser
│   │   └── qradar_parser.py      # QRadar XML parser
│   ├── static/
│   │   ├── index.html            # Web UI
│   │   ├── script.js             # Frontend logic
│   │   └── style.css             # Modern dark theme
│   └── xsiam_analytics.json      # 1,177 XSIAM analytics
├── sample_splunk.json             # Example Splunk export
└── README.md
```

## 🔧 Technical Stack

**Backend:**
- FastAPI - Modern async Python web framework
- Pydantic - Data validation and modeling
- BeautifulSoup4 - HTML parsing for analytics extraction
- pandas - Data processing

**Frontend:**
- Vanilla JavaScript (no frameworks)
- CSS3 with dark mode design
- Responsive layout

## 📊 Coverage Analysis Algorithm

The coverage analyzer uses a weighted scoring system:

```python
total_score = (name_similarity * 0.6) + (keyword_match * 0.4)
```

- **Name Similarity (60%)**: SequenceMatcher comparison of rule names
- **Keyword Matching (40%)**: Correlation with detector tags, ATT&CK tactics, and techniques

Rules with a match score > 30% are considered potential coverage.

## 🧪 Sample Data

The repository includes `sample_splunk.json` with example detection rules:
- Suspicious Login Attempt
- Malware Beaconing

Use this file to test the migration workflow.

## 🙏 Acknowledgments

- Palo Alto Networks for XSIAM Analytics documentation

## ⚠️ Disclaimer

This tool is provided as-is for educational and migration planning purposes. Always verify converted queries in a test environment before deploying to production.

---

**Author**: acesarsr  
**Repository**: https://github.com/acesarsr/XSIAM-Migration-Assistant
