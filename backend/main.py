from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List
import uvicorn
import json
import xml.etree.ElementTree as ET
from models import DetectionRule, MigrationSummary
from converter.spl_to_xql import convert_spl_to_xql
from coverage_analyzer import load_analytics, analyze_rule_coverage
from exporter.content_pack_generator import create_content_pack
from reports.report_generator import generate_csv_report, generate_pdf_report

app = FastAPI(title="XSIAM Migration Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo purposes
rules_db: List[DetectionRule] = []

# Load XSIAM analytics at startup
try:
    xsiam_analytics = load_analytics('xsiam_analytics.json')
    print(f"Loaded {len(xsiam_analytics)} XSIAM analytics")
except Exception as e:
    print(f"Warning: Could not load XSIAM analytics: {e}")
    xsiam_analytics = []

@app.get("/api/rules", response_model=List[DetectionRule])
def get_rules():
    return rules_db

@app.get("/api/coverage/{rule_id}")
def get_coverage(rule_id: str):
    """Analyze coverage for a specific rule"""
    rule = next((r for r in rules_db if r.id == rule_id), None)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    coverage = analyze_rule_coverage(
        {'name': rule.name, 'description': rule.description or ''},
        xsiam_analytics
    )
    return coverage

@app.put("/api/rules/{rule_id}")
async def update_rule(rule_id: str, updated_rule: DetectionRule):
    for i, r in enumerate(rules_db):
        if r.id == rule_id:
            rules_db[i] = updated_rule
            return updated_rule
    raise HTTPException(status_code=404, detail="Rule not found")

@app.post("/api/export/content-pack")
def export_content_pack():
    """Export all rules as XSIAM content pack ZIP"""
    if not rules_db:
        raise HTTPException(status_code=400, detail="No rules to export")
    
    # Convert Pydantic models to dicts
    rules_data = [r.dict() for r in rules_db]
    
    # Generate content pack
    zip_buffer = create_content_pack(rules_data, pack_name="MigratedRules")
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=MigratedRules_ContentPack.zip"}
    )

@app.get("/api/reports/coverage/csv")
def get_coverage_report_csv():
    """Generate CSV coverage report for all rules"""
    if not rules_db:
        raise HTTPException(status_code=400, detail="No rules to analyze")
    
    # Generate coverage for all rules
    coverage_results = []
    for rule in rules_db:
        coverage = analyze_rule_coverage(
            {'name': rule.name, 'description': rule.description or ''},
            xsiam_analytics
        )
        coverage_results.append(coverage)
    
    # Generate CSV
    rules_data = [r.dict() for r in rules_db]
    csv_buffer = generate_csv_report(rules_data, coverage_results)
    
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Coverage_Report.csv"}
    )

@app.get("/api/reports/coverage/pdf")
def get_coverage_report_pdf():
    """Generate PDF coverage report for all rules"""
    if not rules_db:
        raise HTTPException(status_code=400, detail="No rules to analyze")
    
    # Generate coverage for all rules
    coverage_results = []
    for rule in rules_db:
        coverage = analyze_rule_coverage(
            {'name': rule.name, 'description': rule.description or ''},
            xsiam_analytics
        )
        coverage_results.append(coverage)
    
    # Generate PDF
    rules_data = [r.dict() for r in rules_db]
    pdf_buffer = generate_pdf_report(rules_data, coverage_results)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Coverage_Report.pdf"}
    )

@app.post("/api/upload/{platform}")
async def upload_file(platform: str, file: UploadFile = File(...)):
    if platform not in ["splunk", "qradar"]:
        raise HTTPException(status_code=400, detail="Invalid platform")
    
    content = await file.read()
    rules = []
    
    if platform == "splunk":
        # Basic parsing logic for Splunk JSON export
        try:
            data = json.loads(content)
            # Handle both list of dicts or wrapper dict
            items = data if isinstance(data, list) else data.get("results", [])
            for idx, item in enumerate(items):
                converted = convert_spl_to_xql(item.get("search", ""))
                rules.append(DetectionRule(
                    id=f"spl-{idx}",
                    name=item.get("title", f"Splunk Rule {idx}"),
                    description=item.get("description", ""),
                    source_platform="splunk",
                    original_query=item.get("search", ""),
                    converted_query=converted,
                    status="translated" if converted else "pending"
                ))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    elif platform == "qradar":
        # Basic parsing logic for QRadar XML export
        try:
            root = ET.fromstring(content)
            # Assuming standard xml export structure (simplified)
            for idx, item in enumerate(root.findall(".//custom_rule")):
                rules.append(DetectionRule(
                    id=f"qrd-{idx}",
                    name=item.findtext("name", f"QRadar Rule {idx}"),
                    description=item.findtext("description", ""),
                    source_platform="qradar",
                    original_query=item.findtext("rule_data", ""),  # Simplified tag
                    status="pending"
                ))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")

    global rules_db
    rules_db = rules
    return {"message": f"Processed {len(rules)} rules", "count": len(rules)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
