import re

def convert_spl_to_xql(spl_query: str) -> str:
    """
    Basic heuristic conversion from SPL to XQL.
    """
    xql = spl_query.strip()
    
    # 1. index=... -> dataset = ...
    xql = re.sub(r'index\s*=\s*(\w+)', r'dataset = \1_raw', xql)
    
    # 2. sourcetype=... -> dataset = ... (XQL uses dataset for everything usually)
    # If index was already matched, this might be redundant, but XQL is dataset-centric.
    # Let's assume sourcetype maps to a specific dataset or preset.
    xql = re.sub(r'sourcetype\s*=\s*(\S+)', r'filter \1', xql) # simplified
    
    # 3. stats count by ... -> comp count() by ...
    xql = re.sub(r'stats\s+count\s+by\s+', r'comp count() by ', xql)
    
    # 4. | where -> | filter
    xql = xql.replace("| where", "| filter")
    
    # 5. table -> fields
    xql = xql.replace("| table", "| fields")
    
    return xql

