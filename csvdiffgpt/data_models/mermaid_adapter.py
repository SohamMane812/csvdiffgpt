"""Adapter for formatting restructuring recommendations as Mermaid diagrams."""
from typing import Dict, Any, List, Optional, Set, Tuple, cast
import os
import re

from .base import BaseDataModelAdapter, register_model_adapter

@register_model_adapter
class MermaidAdapter(BaseDataModelAdapter):
    """Adapter for formatting restructuring recommendations as Mermaid diagrams."""
    
    def format_recommendations(self, recommendations: List[Dict[str, Any]], metadata: Dict[str, Any], **kwargs) -> str:
        """
        Format restructuring recommendations as a Mermaid ER diagram.
        
        Args:
            recommendations: List of restructuring recommendations
            metadata: Metadata dictionary
            **kwargs: Additional parameters
            
        Returns:
            Mermaid diagram code as a string
        """
        table_name = kwargs.get('table_name', os.path.splitext(os.path.basename(kwargs.get('file_path', 'data.csv')))[0])
        
        # Extract tables and relationships from recommendations
        entities = self._extract_entities(recommendations, table_name, metadata)
        relationships = self._extract_relationships(recommendations, table_name)
        
        # Build Mermaid diagram
        mermaid_lines: List[str] = [
            "```mermaid",
            "erDiagram",
            ""
        ]
        
        # Add entities
        for entity_name, entity_info in entities.items():
            mermaid_lines.append(f"    {entity_name} {{")
            
            for col_name, col_type in entity_info["columns"]:
                # Mark primary keys
                notation = "PK" if col_name in entity_info.get("primary_keys", []) else ""
                # Clean column name to remove special characters
                clean_col_name = re.sub(r'[^\w]', '_', col_name)
                mermaid_lines.append(f"        {col_type} {clean_col_name} {notation}")
            
            mermaid_lines.append("    }")
            mermaid_lines.append("")
        
        # Add relationships
        for rel in relationships:
            entity1 = rel["entity1"]
            entity2 = rel["entity2"]
            cardinality = rel["cardinality"]
            
            mermaid_lines.append(f"    {entity1} {cardinality} {entity2} : \"{rel['label']}\"")
        
        mermaid_lines.append("```")
        
        # Add explanatory notes
        mermaid_lines.append("")
        mermaid_lines.append("## Diagram Notes")
        mermaid_lines.append("")
        mermaid_lines.append("This ER diagram represents the recommended data structure based on the analysis:")
        mermaid_lines.append("")
        
        for entity_name, entity_info in entities.items():
            if entity_info.get("is_new", False):
                mermaid_lines.append(f"- **{entity_name}**: {entity_info.get('description', 'New entity table')}")
        
        mermaid_lines.append("")
        mermaid_lines.append("### Relationship Legend")
        mermaid_lines.append("- `||--o{`: One-to-many relationship")
        mermaid_lines.append("- `}|--|{`: Many-to-many relationship")
        mermaid_lines.append("- `||--||`: One-to-one relationship")
        
        return "\n".join(mermaid_lines)
    
    def _extract_entities(self, recommendations: List[Dict[str, Any]], main_table: str, metadata: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract entities (tables) from recommendations.
        
        Args:
            recommendations: List of restructuring recommendations
            main_table: Name of the main table
            metadata: Metadata dictionary
            
        Returns:
            Dictionary of entities with their columns and keys
        """
        entities: Dict[str, Dict[str, Any]] = {
            main_table: {
                "columns": [],
                "primary_keys": [],
                "is_new": False,
                "description": "Original table"
            }
        }
        
        # Add columns from metadata to main table
        for col_name, col_info in metadata.get("columns", {}).items():
            col_type = col_info.get("type", "")
            
            # Map pandas dtype to a simpler type for Mermaid
            mermaid_type = "string"
            if "int" in col_type:
                mermaid_type = "int"
            elif "float" in col_type:
                mermaid_type = "float"
            elif "bool" in col_type:
                mermaid_type = "boolean"
            elif "datetime" in col_type or "date" in col_type:
                mermaid_type = "date"
            
            entities[main_table]["columns"].append((col_name, mermaid_type))
        
        # Find primary keys for the main table
        for rec in recommendations:
            if rec.get("type") == "relationship" and rec.get("subtype") == "primary_key":
                pk_column = rec.get("columns", [])[0] if rec.get("columns") else None
                if pk_column:
                    primary_keys = cast(List[str], entities[main_table].get("primary_keys", []))
                    primary_keys.append(pk_column)
                    entities[main_table]["primary_keys"] = primary_keys
        
        # Extract entities from normalization recommendations
        for rec in recommendations:
            rec_type = rec.get("type", "")
            rec_subtype = rec.get("subtype", "")
            
            # Handle dimension tables
            if rec_type == "normalization" and rec_subtype == "create_dimension_table":
                entity_name = rec.get("details", {}).get("dimension_table_name", "")
                column = rec.get("columns", [])[0] if rec.get("columns") else None
                
                if entity_name and column:
                    entities[entity_name] = {
                        "columns": [
                            (f"{entity_name}_id", "int"),  # PK
                            (column, "string")             # Value column
                        ],
                        "primary_keys": [f"{entity_name}_id"],
                        "is_new": True,
                        "description": f"Dimension table for {column} values"
                    }
            
            # Handle entity extraction
            elif rec_type == "normalization" and rec_subtype in ["split_entity", "extract_entity_attributes"]:
                entity_name = rec.get("details", {}).get("entity_name", "")
                columns = rec.get("columns", [])
                primary_key = rec.get("details", {}).get("primary_key", "")
                
                if entity_name and columns:
                    # Build column list for the new entity
                    entity_columns: List[Tuple[str, str]] = []
                    
                    # Add primary key if specified, otherwise use generated ID
                    if primary_key:
                        entity_columns.append((primary_key, "int"))
                        primary_keys = [primary_key]
                    else:
                        entity_columns.append((f"{entity_name}_id", "int"))
                        primary_keys = [f"{entity_name}_id"]
                    
                    # Add other columns
                    for col in columns:
                        if col != primary_key:  # Skip PK, already added
                            # Find column type from metadata
                            col_type = "string"  # Default
                            if col in metadata.get("columns", {}):
                                pandas_type = metadata["columns"][col].get("type", "")
                                if "int" in pandas_type:
                                    col_type = "int"
                                elif "float" in pandas_type:
                                    col_type = "float"
                                elif "bool" in pandas_type:
                                    col_type = "boolean"
                                elif "datetime" in pandas_type or "date" in pandas_type:
                                    col_type = "date"
                            
                            # For normalized attributes, strip the prefix
                            if rec_subtype == "extract_entity_attributes" and entity_name in col:
                                display_name = col.replace(f"{entity_name}_", "")
                            else:
                                display_name = col
                                
                            entity_columns.append((display_name, col_type))
                    
                    entities[entity_name] = {
                        "columns": entity_columns,
                        "primary_keys": primary_keys,
                        "is_new": True,
                        "description": f"Extracted {entity_name} entity"
                    }
        
        return entities
    
    def _extract_relationships(self, recommendations: List[Dict[str, Any]], main_table: str) -> List[Dict[str, Any]]:
        """
        Extract relationships from recommendations.
        
        Args:
            recommendations: List of restructuring recommendations
            main_table: Name of the main table
            
        Returns:
            List of relationships between entities
        """
        relationships: List[Dict[str, Any]] = []
        
        # Extract relationships from recommendations
        for rec in recommendations:
            rec_type = rec.get("type", "")
            rec_subtype = rec.get("subtype", "")
            
            # Handle foreign key relationships
            if rec_type == "relationship" and rec_subtype == "foreign_key":
                details = rec.get("details", {})
                child_col = details.get("child_column", "")
                parent_table = details.get("parent_table", "")
                
                if child_col and parent_table:
                    relationships.append({
                        "entity1": main_table,
                        "entity2": parent_table,
                        "cardinality": "||--o{",  # One-to-many
                        "label": child_col
                    })
            
            # Handle dimension tables
            elif rec_type == "normalization" and rec_subtype == "create_dimension_table":
                details = rec.get("details", {})
                dimension_table = details.get("dimension_table_name", "")
                
                if dimension_table:
                    relationships.append({
                        "entity1": main_table,
                        "entity2": dimension_table,
                        "cardinality": "||--o{",  # One-to-many
                        "label": details.get("foreign_key_column", "fk")
                    })
            
            # Handle entity extraction
            elif rec_type == "normalization" and rec_subtype in ["split_entity", "extract_entity_attributes"]:
                details = rec.get("details", {})
                entity_name = details.get("entity_name", "")
                
                if entity_name:
                    # For entity attributes, it's typically a one-to-one relationship
                    # For entity splitting, it's typically one-to-many (child to parent)
                    cardinality = "||--||" if rec_subtype == "extract_entity_attributes" else "||--o{"
                    
                    relationships.append({
                        "entity1": main_table,
                        "entity2": entity_name,
                        "cardinality": cardinality,
                        "label": details.get("primary_key", "id")
                    })
            
            # Handle junction tables
            elif rec_type == "relationship" and rec_subtype == "junction_table":
                details = rec.get("details", {})
                connecting_tables = details.get("connecting_tables", [])
                
                if len(connecting_tables) >= 2:
                    # Add relationships to both parent tables
                    relationships.append({
                        "entity1": main_table,
                        "entity2": connecting_tables[0],
                        "cardinality": "o{--||", 
                        "label": "belongs to"
                    })
                    
                    relationships.append({
                        "entity1": main_table,
                        "entity2": connecting_tables[1],
                        "cardinality": "o{--||",
                        "label": "belongs to"
                    })
        
        return relationships