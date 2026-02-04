"""
Coverage analyzer to match uploaded rules with XSIAM analytics
"""
import json
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

def load_analytics(filepath='xsiam_analytics.json'):
    """Load XSIAM analytics from JSON file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_coverage(rule_name: str, rule_description: str, analytics: List[Dict]) -> List[Tuple[Dict, float]]:
    """
    Calculate coverage by comparing rule with XSIAM analytics
    Returns list of (analytic, similarity_score) tuples
    """
    matches = []
    
    for analytic in analytics:
        analytic_name = analytic.get('Name', '')
        
        # Calculate similarity based on name
        name_similarity = SequenceMatcher(None, rule_name.lower(), analytic_name.lower()).ratio()
        
        # Check for keyword matches in description vs detector tags
        desc_lower = rule_description.lower()
        tags = analytic.get('Detector Tags', '')
        tactics = analytic.get('ATT&CK Tactic', '')
        techniques = analytic.get('ATT&CK Technique', '')
        
        keyword_score = 0
        keywords = [tags, tactics, techniques]
        for kw in keywords:
            if kw and any(word in desc_lower for word in kw.lower().split(', ')):
                keyword_score += 0.2
        
        total_score = (name_similarity * 0.6) + (keyword_score * 0.4)
        
        if total_score > 0.3:  # Only include matches above threshold
            matches.append((analytic, total_score))
    
    # Sort by score descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:5]  # Return top 5 matches

def analyze_rule_coverage(rule: Dict, analytics: List[Dict]) -> Dict:
    """Analyze a single rule for coverage"""
    matches = calculate_coverage(
        rule.get('name', ''),
        rule.get('description', ''),
        analytics
    )
    
    return {
        'rule_name': rule.get('name'),
        'covered': len(matches) > 0,
        'confidence': matches[0][1] if matches else 0,
        'best_match': matches[0][0].get('Name') if matches else None,
        'all_matches': [
            {
                'name': m[0].get('Name'),
                'score': round(m[1], 2),
                'severity': m[0].get('Severity'),
                'tags': m[0].get('Detector Tags'),
                'tactics': m[0].get('ATT&CK Tactic')
            }
            for m in matches
        ]
    }
