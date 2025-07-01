"""Analyzer for identifying normalization opportunities in CSV data."""
from typing import Dict, Any, List, Optional, Tuple, Set
import pandas as pd
import numpy as np
import re

from .base import BaseRestructureAnalyzer, register_analyzer

@register_analyzer
class NormalizationAnalyzer(BaseRestructureAnalyzer):
    """Analyzer for identifying normalization opportunities in CSV data."""
    
    def analyze(self, df: pd.DataFrame, metadata: Dict[str, Any], validation_results: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """
        Analyze the data for normalization opportunities.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            validation_results: Results from validate_raw function
            **kwargs: Additional parameters
            
        Returns:
            List of restructuring recommendations
        """
        recommendations: List[Dict[str, Any]] = []
        
        # 1. Identify potential dimension tables
        # Look for categorical columns with repeating values that could be normalized
        dimension_candidates = self._find_dimension_candidates(df, metadata)
        
        for dim_info in dimension_candidates:
            column = dim_info["column"]
            uniqueness = dim_info["uniqueness"]
            repeat_factor = dim_info["repeat_factor"]
            
            # Generate a normalized table name
            table_name = self._generate_table_name(column)
            id_column = f"{table_name}_id"
            
            # SQL for creating dimension table
            sql_create_dim = [
                f"-- Create dimension table for '{column}'",
                f"CREATE TABLE {table_name} (",
                f"    {id_column} INT PRIMARY KEY,",
                f"    {column} VARCHAR(255) NOT NULL UNIQUE",
                f");"
            ]
            
            # SQL for creating foreign key relationship
            sql_modify_fact = [
                f"-- Add foreign key to main table",
                f"ALTER TABLE your_main_table",
                f"ADD COLUMN {id_column} INT,",
                f"ADD FOREIGN KEY ({id_column}) REFERENCES {table_name}({id_column});"
            ]
            
            # Python code for normalization
            python_code = [
                f"# Create dimension table for '{column}'",
                f"{table_name}_df = pd.DataFrame(df['{column}'].unique(), columns=['{column}'])",
                f"{table_name}_df.reset_index(inplace=True)",
                f"{table_name}_df.rename(columns={{'index': '{id_column}'}}, inplace=True)",
                "",
                f"# Add foreign key to main dataframe",
                f"df = df.merge({table_name}_df, on='{column}', how='left')",
                f"# Optionally, remove the original column",
                f"# df = df.drop(columns=['{column}'])"
            ]
            
            recommendations.append({
                "type": "normalization",
                "subtype": "create_dimension_table",
                "name": f"normalize_{column}_dimension",
                "description": f"Create dimension table for '{column}' which has {uniqueness:.1f}% uniqueness and repeats {repeat_factor:.1f}x on average",
                "severity": "medium",
                "columns": [column],
                "action": "create_dimension_table",
                "details": {
                    "column": column,
                    "uniqueness_percentage": uniqueness,
                    "repeat_factor": repeat_factor,
                    "dimension_table_name": table_name,
                    "foreign_key_column": id_column
                },
                "sql_code": "\n".join(sql_create_dim + [""] + sql_modify_fact),
                "python_code": "\n".join(python_code)
            })
        
        # 2. Identify potential entity splitting
        # Look for columns that seem to belong to a separate entity
        entity_groups = self._find_entity_groups(df, metadata)
        
        for group_info in entity_groups:
            entity_name = group_info["entity_name"]
            columns = group_info["columns"]
            primary_key = group_info.get("primary_key")
            
            # SQL for creating new entity table
            sql_create_entity = [
                f"-- Create new table for '{entity_name}' entity",
                f"CREATE TABLE {entity_name} ("
            ]
            
            # Add primary key if identified
            if primary_key:
                sql_create_entity.append(f"    {primary_key} INT PRIMARY KEY,")
            else:
                sql_create_entity.append(f"    {entity_name}_id SERIAL PRIMARY KEY,")
            
            # Add other columns
            for col in columns:
                if col != primary_key:
                    col_type = "VARCHAR(255)"  # Default type
                    if col in metadata.get("columns", {}):
                        col_meta = metadata["columns"][col]
                        if "int" in col_meta.get("type", ""):
                            col_type = "INT"
                        elif "float" in col_meta.get("type", ""):
                            col_type = "FLOAT"
                        elif "bool" in col_meta.get("type", ""):
                            col_type = "BOOLEAN"
                        elif "date" in col_meta.get("type", ""):
                            col_type = "DATE"
                    
                    sql_create_entity.append(f"    {col} {col_type},")
            
            # Remove trailing comma and close statement
            if sql_create_entity[-1].endswith(","):
                sql_create_entity[-1] = sql_create_entity[-1][:-1]
            sql_create_entity.append(");")
            
            # SQL for relationship
            sql_relationship = []
            if primary_key:
                sql_relationship = [
                    f"-- Add foreign key to main table (if not already there)",
                    f"-- ALTER TABLE your_main_table",
                    f"-- ADD FOREIGN KEY ({primary_key}) REFERENCES {entity_name}({primary_key});"
                ]
            
            # Python code for splitting
            python_code = [
                f"# Create new dataframe for '{entity_name}' entity",
                f"{entity_name}_df = df[{columns}].copy()"
            ]

            if primary_key:
                python_code.append(f"# Use existing '{primary_key}' as the primary key")
            else:
                python_code.extend([
                    f"# Create a new primary key",
                    f"{entity_name}_df.reset_index(inplace=True)",
                    f"{entity_name}_df.rename(columns={{'index': '{entity_name}_id'}}, inplace=True)"
                ])

            col_str = ', '.join([f"'{c}'" for c in columns if c != primary_key])
            python_code.extend([
                f"# Remove these columns from the main dataframe",
                f"# Keep the primary key in both dataframes for the relationship",
                f"main_df = df.drop(columns=[{col_str}])"
            ])

            
            recommendations.append({
                "type": "normalization",
                "subtype": "split_entity",
                "name": f"extract_{entity_name}_entity",
                "description": f"Extract '{entity_name}' as a separate entity with columns: {', '.join(columns)}",
                "severity": "medium",
                "columns": columns,
                "action": "create_entity_table",
                "details": {
                    "entity_name": entity_name,
                    "columns": columns,
                    "primary_key": primary_key
                },
                "sql_code": "\n".join(sql_create_entity + [""] + sql_relationship),
                "python_code": "\n".join(python_code)
            })
        
        # 3. Identify denormalized columns (e.g., "address_line1", "address_city", "address_state")
        denormalized_groups = self._find_denormalized_groups(df)
        
        for group_name, group_columns in denormalized_groups:
            # Generate normalized table name
            table_name = self._generate_table_name(group_name)
            
            # SQL for creating new table
            sql_create_table = [
                f"-- Create table for '{group_name}' attributes",
                f"CREATE TABLE {table_name} (",
                f"    {table_name}_id SERIAL PRIMARY KEY,"
            ]
            
            # Add columns
            for col in group_columns:
                col_suffix = col.replace(f"{group_name}_", "")
                col_type = "VARCHAR(255)"  # Default type
                if col in metadata.get("columns", {}):
                    col_meta = metadata["columns"][col]
                    if "int" in col_meta.get("type", ""):
                        col_type = "INT"
                    elif "float" in col_meta.get("type", ""):
                        col_type = "FLOAT"
                
                sql_create_table.append(f"    {col_suffix} {col_type},")
            
            # Remove trailing comma and close statement
            if sql_create_table[-1].endswith(","):
                sql_create_table[-1] = sql_create_table[-1][:-1]
            sql_create_table.append(");")
            
            # SQL for relationship
            sql_relationship = [
                f"-- Add foreign key to main table",
                f"ALTER TABLE your_main_table",
                f"ADD COLUMN {table_name}_id INT,",
                f"ADD FOREIGN KEY ({table_name}_id) REFERENCES {table_name}({table_name}_id);"
            ]
            
            # Python code for normalization
            col_str = ', '.join([f"'{c}'" for c in group_columns])

            python_code = [
                f"# Create table for '{group_name}' attributes",
                f"{table_name}_df = df[[{col_str}]].copy()",
                f"{table_name}_df.reset_index(inplace=True)",
                f"{table_name}_df.rename(columns={{'index': '{table_name}_id'}}, inplace=True)",
                f"# Rename columns to remove the prefix",
                f"for col in {table_name}_df.columns:",
                f"    if col.startswith('{group_name}_'):",
                f"        {table_name}_df.rename(columns={{col: col.replace('{group_name}_', '')}}, inplace=True)",
                "",
                f"# Add foreign key to main dataframe",
                f"df['{table_name}_id'] = {table_name}_df['{table_name}_id']",
                f"# Remove original columns",
                f"df = df.drop(columns=[{col_str}])"
            ]

            
            
            recommendations.append({
                "type": "normalization",
                "subtype": "extract_entity_attributes",
                "name": f"extract_{group_name}_entity",
                "description": f"Extract '{group_name}' attributes into a separate table: {', '.join([c.replace(f'{group_name}_', '') for c in group_columns])}",
                "severity": "medium",
                "columns": group_columns,
                "action": "create_attribute_table",
                "details": {
                    "entity_name": group_name,
                    "columns": group_columns,
                    "new_table": table_name
                },
                "sql_code": "\n".join(sql_create_table + [""] + sql_relationship),
                "python_code": "\n".join(python_code)
            })
        
        return recommendations
    
    def _find_dimension_candidates(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find columns that would make good dimension tables.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of dictionaries with information about dimension candidates
        """
        candidates: List[Dict[str, Any]] = []
        total_rows = len(df)
        
        # Skip if too small
        if total_rows < 10:
            return candidates
        
        # Analyze each column
        for column, details in metadata.get("columns", {}).items():
            # Skip columns with high null percentage
            if details.get("null_percentage", 0) > 10:
                continue
                
            # Only consider object/string columns with reasonable cardinality
            if "object" in details.get("type", "") and "unique_count" in details:
                unique_count = details["unique_count"]
                
                # Skip columns that are almost all unique (like IDs) or have too few values
                if unique_count < 3 or unique_count > total_rows * 0.5:
                    continue
                
                # Calculate metrics
                uniqueness = (unique_count / total_rows) * 100
                repeat_factor = total_rows / max(1, unique_count)
                
                # Columns that repeat frequently (at least 5 times on average)
                # and aren't too unique (less than 20% unique values)
                if repeat_factor >= 5 and uniqueness < 20:
                    candidates.append({
                        "column": column,
                        "uniqueness": uniqueness,
                        "repeat_factor": repeat_factor,
                        "unique_count": unique_count
                    })
        
        # Sort by potential space savings (higher repeat factor first)
        return sorted(candidates, key=lambda x: x["repeat_factor"], reverse=True)
    
    def _find_entity_groups(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find groups of columns that might represent separate entities.
        
        Args:
            df: Pandas DataFrame
            metadata: Metadata dictionary
            
        Returns:
            List of dictionaries with information about entity groups
        """
        entity_groups = []
        
        # Strategy 1: Look for columns with common prefixes
        prefix_groups = self._group_by_prefix(list(df.columns))
        
        for prefix, columns in prefix_groups.items():
            # Only consider groups with at least 3 columns
            if len(columns) >= 3:
                # Look for a potential primary key in the group
                primary_key = None
                for col in columns:
                    if col.lower().endswith('id') or col.lower().endswith('_id'):
                        # Check if it has high cardinality
                        if col in metadata.get("columns", {}):
                            col_meta = metadata["columns"][col]
                            unique_count = col_meta.get("unique_count", 0)
                            null_count = col_meta.get("nulls", 0)
                            total_rows = metadata.get("total_rows", len(df))
                            
                            # If it's highly unique and not null, it's likely a primary key
                            if unique_count > 0 and null_count == 0 and unique_count / total_rows > 0.9:
                                primary_key = col
                                break
                
                entity_groups.append({
                    "entity_name": prefix,
                    "columns": columns,
                    "primary_key": primary_key
                })
        
        # Strategy 2: Look for potential parent-child relationships
        
        return entity_groups
    
    def _find_denormalized_groups(self, df: pd.DataFrame) -> List[Tuple[str, List[str]]]:
        """
        Find groups of columns that appear to be denormalized attributes of the same entity.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            List of tuples (entity_name, [column_list])
        """
        # Find columns with common prefixes
        prefix_groups = self._group_by_prefix(list(df.columns))
        
        # Filter to prefixes that seem like entities and have multiple related columns
        denormalized_groups = []
        
        for prefix, columns in prefix_groups.items():
            # Only consider groups with at least 2 columns
            if len(columns) >= 2:
                # Check if the columns have a consistent pattern suggesting attributes
                # e.g., address_line1, address_city, address_state
                
                # Get suffixes
                suffixes = [col.replace(f"{prefix}_", "") for col in columns]
                
                # Check if suffixes look like attributes
                attribute_like = any(suffix in ['id', 'name', 'code', 'type', 'desc', 'description', 
                                               'line1', 'line2', 'city', 'state', 'zip', 'country',
                                               'street', 'number', 'postal'] 
                                    for suffix in suffixes)
                
                if attribute_like:
                    denormalized_groups.append((prefix, columns))
        
        return denormalized_groups
    
    def _group_by_prefix(self, column_names: List[str]) -> Dict[str, List[str]]:
        """
        Group column names by common prefixes.
        
        Args:
            column_names: List of column names
            
        Returns:
            Dictionary mapping prefixes to lists of column names
        """
        prefix_groups: Dict[str, List[str]] = {}
        
        for col in column_names:
            # Skip columns that don't have a clear prefix pattern
            if '_' not in col:
                continue
                
            # Extract prefix (part before the last underscore)
            parts = col.split('_')
            if len(parts) >= 2:
                # Use the part before the last underscore as the prefix
                prefix = '_'.join(parts[:-1])
                
                # Skip single-letter prefixes or very long ones
                if len(prefix) <= 1 or len(prefix) > 20:
                    continue
                
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(col)
        
        # Filter out groups with only one column
        return {prefix: cols for prefix, cols in prefix_groups.items() if len(cols) > 1}
    
    def _generate_table_name(self, base_name: str) -> str:
        """
        Generate a suitable table name from a base name.
        
        Args:
            base_name: Base name to convert
            
        Returns:
            Formatted table name
        """
        # Remove any non-alphanumeric characters
        clean_name = re.sub(r'[^\w]', '_', base_name)
        
        # Convert to snake_case if it's in camelCase
        snake_case = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', clean_name).lower()
        
        # Remove leading/trailing underscores
        return snake_case.strip('_')