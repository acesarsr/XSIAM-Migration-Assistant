"""
Database layer for XSIAM Migration Assistant
Provides persistent storage for migration history using SQLite
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json

DB_PATH = Path(__file__).parent / "migration_history.db"


def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Migrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_platform TEXT NOT NULL,
            file_name TEXT,
            total_rules INTEGER DEFAULT 0,
            successful_conversions INTEGER DEFAULT 0,
            failed_conversions INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    
    # Rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            migration_id INTEGER NOT NULL,
            rule_id TEXT NOT NULL,
            rule_name TEXT,
            description TEXT,
            original_query TEXT,
            converted_query TEXT,
            status TEXT,
            coverage_score REAL,
            best_match TEXT,
            FOREIGN KEY (migration_id) REFERENCES migrations(id) ON DELETE CASCADE
        )
    """)
    
    # Coverage results table (detailed match information)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coverage_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            match_name TEXT,
            match_score REAL,
            severity TEXT,
            tags TEXT,
            tactics TEXT,
            FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


def save_migration(source_platform: str, file_name: str, rules_data: List[Dict], coverage_data: List[Dict]) -> int:
    """
    Save a migration with all rules and coverage data
    
    Returns:
        migration_id: The ID of the saved migration
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate statistics
    total_rules = len(rules_data)
    successful = sum(1 for r in rules_data if r.get('status') in ['translated', 'reviewed'])
    failed = total_rules - successful
    
    # Insert migration record
    cursor.execute("""
        INSERT INTO migrations (source_platform, file_name, total_rules, successful_conversions, failed_conversions)
        VALUES (?, ?, ?, ?, ?)
    """, (source_platform, file_name, total_rules, successful, failed))
    
    migration_id = cursor.lastrowid
    
    # Insert rules
    for idx, (rule, coverage) in enumerate(zip(rules_data, coverage_data)):
        cursor.execute("""
            INSERT INTO rules (migration_id, rule_id, rule_name, description, original_query, 
                             converted_query, status, coverage_score, best_match)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            migration_id,
            rule.get('id', f'rule-{idx}'),
            rule.get('name', ''),
            rule.get('description', ''),
            rule.get('original_query', ''),
            rule.get('converted_query', ''),
            rule.get('status', 'pending'),
            coverage.get('confidence', 0.0),
            coverage.get('best_match', None)
        ))
        
        rule_pk = cursor.lastrowid
        
        # Insert coverage matches
        for match in coverage.get('all_matches', [])[:5]:  # Top 5 matches
            cursor.execute("""
                INSERT INTO coverage_results (rule_id, match_name, match_score, severity, tags, tactics)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rule_pk,
                match.get('name', ''),
                match.get('score', 0.0),
                match.get('severity', ''),
                match.get('tags', ''),
                match.get('tactics', '')
            ))
    
    conn.commit()
    conn.close()
    
    return migration_id


def get_all_migrations() -> List[Dict]:
    """Get all migrations with summary information"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, timestamp, source_platform, file_name, total_rules, 
               successful_conversions, failed_conversions
        FROM migrations
        ORDER BY timestamp DESC
    """)
    
    migrations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return migrations


def get_migration_details(migration_id: int) -> Optional[Dict]:
    """Get detailed information about a specific migration"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get migration info
    cursor.execute("""
        SELECT * FROM migrations WHERE id = ?
    """, (migration_id,))
    
    migration = cursor.fetchone()
    if not migration:
        conn.close()
        return None
    
    migration_dict = dict(migration)
    
    # Get all rules for this migration
    cursor.execute("""
        SELECT * FROM rules WHERE migration_id = ?
    """, (migration_id,))
    
    rules = [dict(row) for row in cursor.fetchall()]
    
    # Get coverage results for each rule
    for rule in rules:
        cursor.execute("""
            SELECT match_name, match_score, severity, tags, tactics
            FROM coverage_results
            WHERE rule_id = ?
            ORDER BY match_score DESC
        """, (rule['id'],))
        
        rule['coverage_matches'] = [dict(row) for row in cursor.fetchall()]
    
    migration_dict['rules'] = rules
    conn.close()
    
    return migration_dict


def delete_migration(migration_id: int) -> bool:
    """Delete a migration and all associated data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM migrations WHERE id = ?", (migration_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


def get_migration_stats() -> Dict:
    """Get overall statistics across all migrations"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_migrations,
            SUM(total_rules) as total_rules,
            SUM(successful_conversions) as total_successful,
            AVG(successful_conversions * 1.0 / total_rules) as avg_success_rate
        FROM migrations
    """)
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'total_migrations': row[0] or 0,
        'total_rules': row[1] or 0,
        'total_successful': row[2] or 0,
        'avg_success_rate': round((row[3] or 0) * 100, 1)
    }


# Initialize database on module import
init_database()
