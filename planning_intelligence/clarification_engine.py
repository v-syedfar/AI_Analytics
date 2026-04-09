"""
Intelligent Clarification Engine for Copilot
Guides users through incomplete queries using real dataset values.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ClarificationEngine:
    """Detects missing context and guides user through interactive clarification."""
    
    def __init__(self):
        self.required_context = {
            'record_detail': ['locationId', 'materialGroup'],  # LOCID, EQUIPCAT
            'supplier_query': ['locationId'],  # LOCID minimum
            'material_query': ['materialGroup'],  # EQUIPCAT
            'comparison': ['entity1', 'entity2'],  # 2 entities
            'root_cause': ['locationId'],  # LOCID
            'location_analysis': ['locationId'],  # LOCID
        }
    
    def extract_available_values(self, detail_records: List[Dict]) -> Dict[str, List[str]]:
        """Extract unique values from dataset for each dimension."""
        available = {
            'locations': set(),
            'material_groups': set(),
            'materials': set(),
            'suppliers': set(),
        }
        
        for record in detail_records:
            if record.get('locationId'):
                available['locations'].add(record['locationId'])
            if record.get('equipmentCategory'):
                available['material_groups'].add(record['equipmentCategory'])
            if record.get('materialId'):
                available['materials'].add(record['materialId'])
            if record.get('supplierId'):
                available['suppliers'].add(record['supplierId'])
        
        # Convert sets to sorted lists
        return {
            'locations': sorted(list(available['locations'])),
            'material_groups': sorted(list(available['material_groups'])),
            'materials': sorted(list(available['materials'])),
            'suppliers': sorted(list(available['suppliers'])),
        }
    
    def get_materials_for_group(self, detail_records: List[Dict], material_group: str) -> List[str]:
        """Get all materials in a specific material group."""
        materials = set()
        for record in detail_records:
            if record.get('equipmentCategory') == material_group:
                if record.get('materialId'):
                    materials.add(record['materialId'])
        return sorted(list(materials))
    
    def get_materials_at_location(self, detail_records: List[Dict], location_id: str) -> List[str]:
        """Get all materials at a specific location."""
        materials = set()
        for record in detail_records:
            if record.get('locationId') == location_id:
                if record.get('materialId'):
                    materials.add(record['materialId'])
        return sorted(list(materials))
    
    def get_locations_for_material(self, detail_records: List[Dict], material_id: str) -> List[str]:
        """Get all locations where a material exists."""
        locations = set()
        for record in detail_records:
            if record.get('materialId') == material_id:
                if record.get('locationId'):
                    locations.add(record['locationId'])
        return sorted(list(locations))
    
    def get_material_groups_at_location(self, detail_records: List[Dict], location_id: str) -> List[str]:
        """Get all material groups at a specific location."""
        groups = set()
        for record in detail_records:
            if record.get('locationId') == location_id:
                if record.get('equipmentCategory'):
                    groups.add(record['equipmentCategory'])
        return sorted(list(groups))
    
    def get_suppliers_at_location(self, detail_records: List[Dict], location_id: str) -> List[str]:
        """Get all suppliers at a specific location."""
        suppliers = set()
        for record in detail_records:
            if record.get('locationId') == location_id:
                if record.get('supplierId'):
                    suppliers.add(record['supplierId'])
        return sorted(list(suppliers))
    
    def detect_missing_context(
        self,
        query_type: str,
        extracted_entities: Dict[str, Optional[str]],
        detail_records: List[Dict]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Detect if required context is missing.
        
        Returns:
            (has_missing_context, next_clarification_step, clarification_data)
        """
        logger.info(f"Detecting missing context for {query_type}")
        logger.info(f"Extracted entities: {extracted_entities}")
        
        # Get available values from dataset
        available = self.extract_available_values(detail_records)
        
        # Check each query type
        if query_type == 'record_detail':
            # Need: location + material group (minimum)
            location = extracted_entities.get('locationId')
            material_group = extracted_entities.get('materialGroup')
            material_id = extracted_entities.get('materialId')
            
            if not location:
                return (True, 'ask_location', {
                    'available_locations': available['locations'],
                    'message': 'To analyze record details, please select a location.',
                })
            
            if not material_group and not material_id:
                groups = self.get_material_groups_at_location(detail_records, location)
                return (True, 'ask_material_group', {
                    'available_groups': groups,
                    'location': location,
                    'message': f'Now select a material group at {location}.',
                })
            
            if not material_id and material_group:
                materials = self.get_materials_for_group(detail_records, material_group)
                return (True, 'ask_material_id', {
                    'available_materials': materials,
                    'location': location,
                    'material_group': material_group,
                    'message': f'Now select a material in {material_group} at {location}.',
                })
        
        elif query_type == 'supplier_query':
            # Need: location (minimum)
            location = extracted_entities.get('locationId')
            
            if not location:
                return (True, 'ask_location', {
                    'available_locations': available['locations'],
                    'message': 'To analyze suppliers, please select a location.',
                })
        
        elif query_type == 'material_query':
            # Need: material group (minimum)
            material_group = extracted_entities.get('materialGroup')
            material_id = extracted_entities.get('materialId')
            
            if not material_id and not material_group:
                return (True, 'ask_material_group', {
                    'available_groups': available['material_groups'],
                    'message': 'To analyze materials, please select a material group.',
                })
        
        elif query_type == 'comparison':
            # Need: 2 entities of same type
            entity1 = extracted_entities.get('entity1')
            entity2 = extracted_entities.get('entity2')
            
            if not entity1 or not entity2:
                return (True, 'ask_comparison_entities', {
                    'available_locations': available['locations'],
                    'available_materials': available['materials'],
                    'available_groups': available['material_groups'],
                    'message': 'To compare, please select two entities.',
                })
        
        elif query_type == 'root_cause':
            # Need: location
            location = extracted_entities.get('locationId')
            
            if not location:
                return (True, 'ask_location', {
                    'available_locations': available['locations'],
                    'message': 'To analyze root cause, please select a location.',
                })
        
        # No missing context
        return (False, None, None)
    
    def build_clarification_response(
        self,
        step: str,
        clarification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build interactive clarification response."""
        
        response = {
            'clarification_needed': True,
            'step': step,
            'message': clarification_data.get('message', ''),
            'options': [],
            'context': {},
        }
        
        if step == 'ask_location':
            response['options'] = [
                {'value': loc, 'label': loc}
                for loc in clarification_data.get('available_locations', [])
            ]
            response['context']['field'] = 'locationId'
        
        elif step == 'ask_material_group':
            response['options'] = [
                {'value': group, 'label': group}
                for group in clarification_data.get('available_groups', [])
            ]
            response['context']['field'] = 'materialGroup'
            response['context']['location'] = clarification_data.get('location')
        
        elif step == 'ask_material_id':
            response['options'] = [
                {'value': mat, 'label': mat}
                for mat in clarification_data.get('available_materials', [])
            ]
            response['context']['field'] = 'materialId'
            response['context']['location'] = clarification_data.get('location')
            response['context']['material_group'] = clarification_data.get('material_group')
        
        elif step == 'ask_comparison_entities':
            response['options'] = [
                {'category': 'Locations', 'values': [
                    {'value': loc, 'label': loc}
                    for loc in clarification_data.get('available_locations', [])
                ]},
                {'category': 'Materials', 'values': [
                    {'value': mat, 'label': mat}
                    for mat in clarification_data.get('available_materials', [])
                ]},
                {'category': 'Material Groups', 'values': [
                    {'value': group, 'label': group}
                    for group in clarification_data.get('available_groups', [])
                ]},
            ]
            response['context']['field'] = 'comparison_entities'
        
        return response
    
    def validate_context_complete(
        self,
        query_type: str,
        extracted_entities: Dict[str, Optional[str]]
    ) -> bool:
        """Check if all required context is available."""
        required = self.required_context.get(query_type, [])
        
        for field in required:
            if not extracted_entities.get(field):
                return False
        
        return True
