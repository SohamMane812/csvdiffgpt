"""Analyzer for identifying potential relationships between columns."""
from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd
import numpy as np
import re

from .base import BaseRestructureAnalyzer, register_analyzer

@register_analyzer
class RelationshipAnalyzer(BaseRestructureAnalyzer):
    """Analyzer for identifying potential relationships between columns."""
    
    def analyze(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Analyze the data for potential relationships.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of restructuring recommendations
        """
        recommendations: List[Dict[str, Any]] = []
        
        # 1. Identify potential primary keys
        primary_keys = self._find_potential_primary_keys(df, metadata)
        
        for col, uniqueness in primary_keys:
            recommendations.append({
                "type": "relationship",
                "subtype": "primary_key",
                "name": f"define_{col}_as_primary_key",
                "description": f"Column '{col}' is a good primary key candidate ({uniqueness:.1f}% unique values, no nulls)",
                "severity": "high",
                "columns": [col],
                "action": "define_primary_key",
                "details": {
                    "column": col,
                    "uniqueness_percentage": uniqueness
                },
                "sql_code": f"-- Define primary key\nALTER TABLE your_table ADD PRIMARY KEY ({col});",
                "python_code": f"# Note: '{col}' is a good primary key\n# In a database, you would define it as:\n# ALTER TABLE your_table ADD PRIMARY KEY ({col});"
            })
        
        # 2. Identify potential foreign keys
        foreign_keys = self._find_potential_foreign_keys(df, metadata)
        
        for fk_info in foreign_keys:
            child_col = fk_info["child_column"]
            parent_col = fk_info["parent_column"]
            parent_table = fk_info["parent_table"]
            match_percentage = fk_info["match_percentage"]
            
            recommendations.append({
                "type": "relationship",
                "subtype": "foreign_key",
                "name": f"define_{child_col}_as_foreign_key",
                "description": f"Column '{child_col}' appears to be a foreign key to {parent_table}.{parent_col} ({match_percentage:.1f}% match)",
                "severity": "medium",
                "columns": [child_col],
                "action": "define_foreign_key",
                "details": fk_info,
                "sql_code": f"-- Define foreign key relationship\nALTER TABLE your_table\nADD CONSTRAINT fk_{child_col}\nFOREIGN KEY ({child_col}) REFERENCES {parent_table}({parent_col});",
                "python_code": f"# Note: '{child_col}' appears to be a foreign key to {parent_table}.{parent_col}\n# In a database, you would define it as:\n# ALTER TABLE your_table ADD FOREIGN KEY ({child_col}) REFERENCES {parent_table}({parent_col});"
            })
        
        # 3. Identify potential junction tables (for many-to-many relationships)
        junction_tables = self._identify_potential_junction_table(df, metadata)
        
        if junction_tables:
            cols = [info["column"] for info in junction_tables]
            table1 = junction_tables[0]["references"]
            table2 = junction_tables[1]["references"] if len(junction_tables) > 1 else "unknown_table"
            
            recommendations.append({
                "type": "relationship",
                "subtype": "junction_table",
                "name": "define_junction_table",
                "description": f"This table appears to be a junction table connecting {table1} and {table2}",
                "severity": "low",
                "columns": cols,
                "action": "define_junction_table",
                "details": {
                    "connecting_tables": [table1, table2],
                    "key_columns": cols
                },
                "sql_code": f"-- This appears to be a junction table\n-- Ensure proper foreign keys are defined\nALTER TABLE your_table\nADD CONSTRAINT fk_{cols[0]}\nFOREIGN KEY ({cols[0]}) REFERENCES {table1}(id);\n\nALTER TABLE your_table\nADD CONSTRAINT fk_{cols[1] if len(cols) > 1 else 'col2'}\nFOREIGN KEY ({cols[1] if len(cols) > 1 else 'col2'}) REFERENCES {table2}(id);",
                "python_code": f"# Note: This table appears to be a junction table\n# In a database, you would define it with foreign keys to both parent tables"
            })
        
        # 4. Identify columns that should be indexed
        index_candidates = self._find_index_candidates(df, metadata)
        
        for col, reason in index_candidates:
            recommendations.append({
                "type": "relationship",
                "subtype": "create_index",
                "name": f"create_index_{col}",
                "description": f"Column '{col}' should have an index: {reason}",
                "severity": "low",
                "columns": [col],
                "action": "create_index",
                "details": {
                    "column": col,
                    "reason": reason
                },
                "sql_code": f"-- Create index on frequently queried column\nCREATE INDEX idx_{col} ON your_table ({col});",
                "python_code": f"# Note: Column '{col}' should be indexed in a database\n# CREATE INDEX idx_{col} ON your_table ({col});"
            })
        
        return recommendations
    
    def _find_potential_primary_keys(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Find columns that could serve as primary keys.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of tuples (column_name, uniqueness_percentage)
        """
        candidates: List[Tuple[str, float]] = []
        total_rows = metadata.get("total_rows", len(df))
        
        # Skip if dataframe is empty
        if total_rows == 0:
            return candidates
            
        for column, details in metadata.get("columns", {}).items():
            # Primary key criteria: 
            # 1. No nulls
            # 2. High uniqueness (>95%)
            # 3. Name suggests ID (but not required)
            
            null_count = details.get("nulls", 0)
            unique_count = details.get("unique_count", 0)
            
            # Skip columns with nulls
            if null_count > 0:
                continue
                
            # Calculate uniqueness
            uniqueness = (unique_count / total_rows) * 100
            
            # Check uniqueness threshold (95% unique or higher)
            if uniqueness >= 95:
                # Score higher if the name suggests ID
                is_id_column = any(id_term in column.lower() for id_term in ['id', 'key', 'code', 'uuid', 'guid'])
                
                candidates.append((column, uniqueness))
        
        # Sort by uniqueness (highest first)
        return sorted(candidates, key=lambda x: x[1], reverse=True)
    
    def _find_potential_foreign_keys(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find columns that could be foreign keys.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of dictionaries with foreign key information
        """
        # Without multiple tables, we can only make basic inferences
        candidates: List[Dict[str, Any]] = []
        
        for column, details in metadata.get("columns", {}).items():
            # Look for columns that might be foreign keys:
            # 1. Names ending with _id but not 'id' itself
            # 2. Has some duplication (not all unique like a PK would be)
            # 3. Not too many nulls
            
            if column.lower().endswith('_id') and column.lower() != 'id':
                null_percentage = details.get("null_percentage", 0)
                unique_count = details.get("unique_count", 0)
                total_rows = metadata.get("total_rows", len(df))
                
                # Only if there aren't too many nulls
                if null_percentage <= 10:
                    # Estimate what table this might reference
                    # Extract the prefix (e.g., 'customer_id' -> 'customer')
                    reference_table = column[:-3]  # Remove '_id'
                    
                    # Format for SQL naming convention
                    reference_table = reference_table.lower().replace(' ', '_')
                    
                    # We don't know the exact match percentage without the referenced table,
                    # so we estimate based on cardinality
                    distinctness = (unique_count / total_rows) * 100
                    
                    candidates.append({
                        "child_column": column,
                        "parent_column": "id",  # Assuming standard convention
                        "parent_table": reference_table,
                        "match_percentage": 100,  # Placeholder
                        "distinct_values": unique_count,
                        "distinct_percentage": distinctness
                    })
        
        return candidates
    
    def _identify_potential_junction_table(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Determine if this table appears to be a junction table (for many-to-many relationships).
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of dictionaries with information about foreign key columns if it's a junction table, empty list otherwise
        """
        # Junction table characteristics:
        # 1. Small number of columns (typically 2-3, plus maybe metadata)
        # 2. Contains at least 2 foreign key columns (ending in _id)
        # 3. The primary key is often a composite of the foreign keys
        
        if len(df.columns) > 5:
            # Too many columns to be a simple junction table
            return []
        
        # Find potential foreign key columns
        foreign_key_cols: List[Dict[str, Any]] = []
        
        for column, details in metadata.get("columns", {}).items():
            if column.lower().endswith('_id'):
                # Extract the referenced table name
                referenced_table = column[:-3]  # Remove '_id'
                
                foreign_key_cols.append({
                    "column": column,
                    "references": referenced_table,
                    "distinct_values": details.get("unique_count", 0)
                })
        
        # If we have at least 2 potential foreign keys, this might be a junction table
        if len(foreign_key_cols) >= 2:
            return foreign_key_cols
        
        return []
    
    def _find_index_candidates(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Find columns that would benefit from indexes.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of tuples (column_name, reason)
        """
        candidates: List[Tuple[str, str]] = []
        
        # 1. Foreign keys should be indexed
        for column, details in metadata.get("columns", {}).items():
            if column.lower().endswith('_id') and column.lower() != 'id':
                candidates.append((column, "Foreign key columns should be indexed for faster joins"))
        
        # 2. Columns with selective but not unique values
        for column, details in metadata.get("columns", {}).items():
            # Skip primary key candidates or already recommended foreign keys
            if any(c[0] == column for c in candidates):
                continue
                
            unique_count = details.get("unique_count", 0)
            total_rows = metadata.get("total_rows", len(df))
            
            if total_rows > 0:
                uniqueness = (unique_count / total_rows) * 100
                
                # Columns with reasonable selectivity (5-80% unique values)
                if 5 <= uniqueness <= 80:
                    # Prioritize columns that are likely to be used in queries
                    is_query_column = any(term in column.lower() for term in 
                                         ['date', 'time', 'year', 'month', 'status', 'type', 
                                          'category', 'region', 'state', 'country', 'name'])
                    
                    if is_query_column:
                        candidates.append((column, f"Commonly queried column with good selectivity ({uniqueness:.1f}% unique values)"))
        
        return candidates