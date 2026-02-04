from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DetectionRule(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source_platform: str  # "splunk" | "qradar"
    original_query: str
    converted_query: Optional[str] = None
    status: str = "pending"  # pending, reviewed, exported
    severity: Optional[str] = "medium"
    tags: List[str] = []

class MigrationSummary(BaseModel):
    total_rules: int
    converted_rules: int
    platform: str
