"""
Enhanced Intent Parser with Context Tracking
Integrates with clarification engine for intelligent query handling.
"""

import logging
import re
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)


class EnhancedIntentParser:
    """Parse queries and extract entities with context awareness."""
    
    def __init__(self):
        self.location_pattern = r'\b([A-Z]+\d+_[A-Z0-9]+|LOC\d+)\b'
        self.material_pattern = r'\b(C\d{8}-\d{3}|MAT[\w\-]*)\b'
        self.material_group_pattern = r'\b(UPS|MVSXRM|LVS|EPMS|ATS|BAS|GEN|BUS|MVS|AHU|HAC|ACC|CRAH|CDU|AHF|TCP|PDU|CT|EHOUSE|WCC|PUMP|VALVE)\b'
        self.supplier_pattern = r'\b(\d+_[A-Z]+)\b'
    
    def parse_query(self, question: str) -> Tuple[str, Dict[str, Optional[str]]]:
        """
        Parse query and extract intent + entities.
        
        Returns:
            (query_type, extracted_entities)
        """
        q = question.lower()
        
        # Extract entities
        entities = {
            'locationId': self._extract_location(question),
            'materialId': self._extract_material_id(question),
            'materialGroup': self._extract_material_group(question),
            'supplierId': self._extract_supplier(question),
            'entity1': None,
            'entity2': None,
        }
        
        # Determine query type
        query_type = self._classify_intent(q, entities)
        
        logger.info(f"Parsed query: type={query_type}, entities={entities}")
        
        return query_type, entities
    
    def _extract_location(self, question: str) -> Optional[str]:
        """Extract location ID from question."""
        match = re.search(self.location_pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
    
    def _extract_material_id(self, question: str) -> Optional[str]:
        """Extract material ID from question."""
        match = re.search(self.material_pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
    
    def _extract_material_group(self, question: str) -> Optional[str]:
        """Extract material group from question."""
        match = re.search(self.material_group_pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
    
    def _extract_supplier(self, question: str) -> Optional[str]:
        """Extract supplier ID from question."""
        match = re.search(self.supplier_pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
    
    def _classify_intent(self, q: str, entities: Dict) -> str:
        """Classify query intent based on keywords and entities."""
        
        # Comparison queries
        if any(word in q for word in ['compare', 'vs', 'versus', 'compared to']):
            return 'comparison'
        
        # Record detail queries
        if any(word in q for word in ['what changed', 'show', 'current vs previous']):
            if entities['materialId'] or entities['materialGroup']:
                return 'record_detail'
        
        # Supplier queries
        if any(word in q for word in ['supplier', 'suppliers']):
            return 'supplier_query'
        
        # Material queries
        if any(word in q for word in ['material', 'materials', 'form factor', 'bod']):
            return 'material_query'
        
        # Root cause queries
        if any(word in q for word in ['why', 'driving', 'cause', 'reason']):
            return 'root_cause'
        
        # Location queries
        if any(word in q for word in ['location', 'locations', 'hotspot']):
            return 'location_analysis'
        
        # Default
        return 'summary'
    
    def extract_comparison_pair(self, question: str) -> Optional[Tuple[str, str]]:
        """Extract two entities being compared."""
        # Pattern: "entity1 vs entity2"
        pattern = r'(\S+)\s+(?:vs|versus|compared?\s+to)\s+(\S+)'
        match = re.search(pattern, question, re.IGNORECASE)
        
        if match:
            entity1 = match.group(1).upper()
            entity2 = match.group(2).upper()
            return (entity1, entity2)
        
        return None
    
    def update_entities_from_user_selection(
        self,
        entities: Dict[str, Optional[str]],
        field: str,
        value: str
    ) -> Dict[str, Optional[str]]:
        """Update entities based on user selection."""
        entities[field] = value
        return entities
