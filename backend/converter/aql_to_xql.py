"""
AQL to XQL Converter
Converts QRadar AQL (Ariel Query Language) queries to Cortex XQL

Key Differences:
- AQL uses SELECT FROM WHERE syntax (SQL-like)
- XQL uses dataset filtering and field selection
- Field names need mapping from QRadar to XDR
"""
import re
from typing import Dict, Optional

# QRadar to XDR field mapping
FIELD_MAPPINGS = {
    # Network fields
    "sourceip": "action_local_ip",
    "destinationip": "action_remote_ip",
    "sourceport": "action_local_port",
    "destinationport": "action_remote_port",
    "protocol": "action_network_protocol",
    
    # User/Identity fields
    "username": "actor_effective_username",
    "userid": "actor_effective_user_sid",
    "domainname": "actor_primary_user_upn_prefix",
    
    # Process fields
    "processname": "causality_actor_process_image_name",
    "processid": "causality_actor_process_os_pid",
    "commandline": "causality_actor_process_command_line",
    
    # File fields
    "filename": "action_file_name",
    "filepath": "action_file_path",
    "filesize": "action_file_size",
    
    # Event fields
    "eventname": "event_type",
    "category": "event_sub_type",
    "severity": "alert_severity",
    "logsourcename": "agent_hostname",
    
    # Time fields
    "starttime": "event_timestamp",
    "endtime": "event_timestamp",
    
    # Additional common fields
    "hostname": "agent_hostname",
    "macaddress": "action_local_mac_address",
    "url": "action_url",
    "domain": "dns_query_name",
}

# Event category mappings (QRadar categories to XDR event types)
CATEGORY_MAPPINGS = {
    "1001": "network",  # Network Activity
    "2000": "process",  # Process
    "3000": "file",     # File
    "4000": "authentication",  # Authentication
    "5000": "user",     # User Activity
    "6000": "system",   # System
}


def map_field(aql_field: str) -> str:
    """Map AQL field name to XQL field name"""
    field_lower = aql_field.lower().strip()
    return FIELD_MAPPINGS.get(field_lower, aql_field)


def parse_select_clause(select_clause: str) -> list:
    """Extract fields from SELECT clause"""
    # Handle SELECT * or SELECT field1, field2, ...
    if '*' in select_clause:
        return []  # Return empty to indicate all fields
    
    fields = [f.strip() for f in select_clause.split(',')]
    return [map_field(f) for f in fields if f]


def parse_where_clause(where_clause: str) -> str:
    """Convert WHERE clause to XQL filter"""
    # Replace AND/OR
    xql_filter = where_clause
    xql_filter = re.sub(r'\bAND\b', 'and', xql_filter, flags=re.IGNORECASE)
    xql_filter = re.sub(r'\bOR\b', 'or', xql_filter, flags=re.IGNORECASE)
    
    # Replace field names
    for aql_field, xql_field in FIELD_MAPPINGS.items():
        # Use word boundaries to avoid partial replacements
        xql_filter = re.sub(
            rf'\b{aql_field}\b',
            xql_field,
            xql_filter,
            flags=re.IGNORECASE
        )
    
    # Convert LIKE to contains
    xql_filter = re.sub(r'\bLIKE\b\s+', 'contains ', xql_filter, flags=re.IGNORECASE)
    
    # Convert category numbers to event types
    for cat_num, event_type in CATEGORY_MAPPINGS.items():
        xql_filter = re.sub(
            rf'category\s*=\s*{cat_num}',
            f'event_type = "{event_type}"',
            xql_filter,
            flags=re.IGNORECASE
        )
    
    return xql_filter


def convert_aql_to_xql(aql_query: str) -> Optional[str]:
    """
    Convert QRadar AQL query to Cortex XQL
    
    Args:
        aql_query: AQL query string
        
    Returns:
        XQL query string or None if conversion fails
    """
    if not aql_query or not aql_query.strip():
        return None
    
    try:
        # Normalize the query
        query = aql_query.strip()
        
        # Basic AQL pattern: SELECT ... FROM ... WHERE ...
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', query, re.IGNORECASE | re.DOTALL)
        from_match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
        where_match = re.search(r'WHERE\s+(.+)', query, re.IGNORECASE | re.DOTALL)
        
        if not select_match:
            return None
        
        select_clause = select_match.group(1).strip()
        from_table = from_match.group(1).strip().lower() if from_match else "events"
        where_clause = where_match.group(1).strip() if where_match else ""
        
        # Parse SELECT fields
        fields = parse_select_clause(select_clause)
        
        # Start building XQL query
        xql_parts = []
        
        # Dataset selection (FROM events -> dataset = xdr_data)
        if from_table in ["events", "flows"]:
            xql_parts.append("dataset = xdr_data")
        else:
            xql_parts.append(f"dataset = {from_table}")
        
        # Add filters from WHERE clause
        if where_clause:
            xql_filter = parse_where_clause(where_clause)
            xql_parts.append(f"filter {xql_filter}")
        
        # Add field selection
        if fields:
            fields_str = ", ".join(fields)
            xql_parts.append(f"fields {fields_str}")
        
        # Combine into final XQL query
        xql_query = " | ".join(xql_parts)
        
        return xql_query
        
    except Exception as e:
        print(f"AQL conversion error: {e}")
        return None
