"""
XSIAM API Client
Handles authentication and direct rule uploads to XSIAM tenant
"""
import requests
from typing import Dict, Optional
import json


class XSIAMClient:
    """Client for interacting with XSIAM API"""
    
    def __init__(self, fqdn: str, api_key: str, api_key_id: str):
        """
        Initialize XSIAM API client
        
        Args:
            fqdn: Fully Qualified Domain Name of your XSIAM tenant
            api_key: XSIAM API Key
            api_key_id: XSIAM API Key ID
        """
        self.fqdn = fqdn
        self.api_key = api_key
        self.api_key_id = api_key_id
        self.base_url = f"https://api-{fqdn}/xsiam/public/v1"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            "Authorization": self.api_key,
            "x-xdr-auth-id": self.api_key_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def test_connection(self) -> Dict:
        """
        Test API connection and credentials
        
        Returns:
            Dict with status and message
        """
        try:
            # Try a simple API endpoint to test auth
            response = requests.get(
                f"{self.base_url}/healthcheck",
                headers=self._get_headers(),
timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Successfully connected to XSIAM"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed. Check your API credentials."
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed with status {response.status_code}"
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def upload_correlation_rule(self, rule_data: Dict) -> Dict:
        """
        Upload a correlation rule to XSIAM
        
        Args:
            rule_data: Dictionary containing rule information
                - name: Rule name
                - xql_query: XQL query string
                - description: Rule description
                - severity: Rule severity (low/medium/high/critical)
                
        Returns:
            Dict with success status and message
        """
        try:
            # Prepare rule payload for XSIAM API
            payload = {
                "name": rule_data.get("name", "Migrated Rule"),
                "description": rule_data.get("description", ""),
                "xql_query": rule_data.get("converted_query", ""),
                "severity": rule_data.get("severity", "medium"),
                "status": "enabled",
                "metadata": {
                    "source": "migration_assistant",
                    "original_platform": rule_data.get("source_platform", "unknown")
                }
            }
            
            # Make API request to create correlation rule
            response = requests.post(
                f"{self.base_url}/correlation_rules",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "message": "Rule uploaded successfully",
                    "rule_id": response.json().get("rule_id")
                }
            else:
                return {
                    "success": False,
                    "message": f"Upload failed: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Upload error: {str(e)}"
            }
    
    def bulk_upload_rules(self, rules: list) -> Dict:
        """
        Upload multiple rules to XSIAM
        
        Args:
            rules: List of rule dictionaries
            
        Returns:
            Dict with results summary
        """
        results = {
            "total": len(rules),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        for rule in rules:
            result = self.upload_correlation_rule(rule)
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "rule": rule.get("name", "Unknown"),
                    "error": result["message"]
                })
        
        return results
