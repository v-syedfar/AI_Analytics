"""
Reasoning Engine - Query-Aware Intelligence Layer

Replaces template-based response generation with dynamic, reasoning-driven outputs.
Implements strict query → intent → execution flow with accurate computation.

Key Principles:
1. Parse question strictly - extract entities with high precision
2. Route to correct computation - no fallback to global summary
3. Compute scoped metrics - only relevant to query scope
4. Generate dynamic responses - no repeated templates
5. Include reasoning - WHY not just WHAT
"""

import logging
import re
from typing import Tuple, Optional, List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


# ============================================================================
# STEP 1: STRICT ENTITY EXTRACTION
# ============================================================================

class EntityExtractor:
    """Extract entities with high precision from questions."""
    
    @staticmethod
    def extract_location(question: str) -> Optional[str]:
        """Extract location ID (LOCID format: XXX##_F##C##)."""
        patterns = [
            r'\blocation\s+([A-Z]{3}\d{2}_F\d{2}C\d{2})',
            r'\bat\s+([A-Z]{3}\d{2}_F\d{2}C\d{2})',
            r'\b([A-Z]{3}\d{2}_F\d{2}C\d{2})\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    @staticmethod
    def extract_material_id(question: str) -> Optional[str]:
        """Extract material ID (format: C########-###)."""
        pattern = r'\b(C\d{8}-\d{3})\b'
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
    
    @staticmethod
    def extract_material_group(question: str) -> Optional[str]:
        """Extract material group (equipment category)."""
        categories = ['UPS', 'MVSXRM', 'LVS', 'EPMS', 'ATS', 'BAS', 'GEN', 'BUS', 
                     'MVS', 'AHU', 'HAC', 'ACC', 'CRAH', 'CDU', 'AHF', 'TCP', 'PDU', 'CT']
        q = question.upper()
        for cat in categories:
            if cat in q:
                return cat
        return None
    
    @staticmethod
    def extract_supplier(question: str) -> Optional[str]:
        """Extract supplier ID (format: ###_REGION)."""
        pattern = r'\b(\d{3}_[A-Z]+)\b'
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None
    
    @staticmethod
    def extract_comparison_pair(question: str) -> Optional[Tuple[str, str]]:
        """Extract two entities being compared."""
        # Match: "X vs Y" or "X versus Y" or "X compared to Y"
        pattern = r'([\w\-]+)\s+(?:vs|versus|compared?\s+to)\s+([\w\-]+)'
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            return (match.group(1).upper(), match.group(2).upper())
        return None


# ============================================================================
# STEP 2: STRICT INTENT CLASSIFICATION
# ============================================================================

class IntentClassifier:
    """Classify question intent with high precision."""
    
    @staticmethod
    def classify(question: str) -> str:
        """
        Classify intent strictly.
        Returns: list | compare | explain_why | trend | root_cause | record_detail
        """
        q = question.lower()
        
        # Comparison intent
        if any(w in q for w in ['compare', ' vs ', 'versus', 'compared to', 'difference']):
            return 'compare'
        
        # List intent
        if any(w in q for w in ['list', 'show', 'which', 'what are']) and not any(w in q for w in ['why', 'cause']):
            return 'list'
        
        # Root cause intent
        if any(w in q for w in ['why', 'cause', 'reason', 'driving', 'driven']):
            return 'root_cause'
        
        # Trend intent
        if any(w in q for w in ['trend', 'forecast', 'increase', 'decrease', 'surge', 'spike']):
            return 'trend'
        
        # Record detail intent
        if any(w in q for w in ['what changed', 'current vs previous', 'detail', 'record']):
            return 'record_detail'
        
        # Default
        return 'summary'


# ============================================================================
# STEP 3: SCOPED COMPUTATION
# ============================================================================

class ScopedComputation:
    """Compute metrics scoped to query context only."""
    
    @staticmethod
    def compute_location_metrics(records: List[Dict], location: str) -> Dict[str, Any]:
        """Compute metrics for a specific location only."""
        location_records = [r for r in records if (r.get('locationId') or '').upper() == location.upper()]
        
        if not location_records:
            return {'error': f'No records found for location {location}'}
        
        changed = [r for r in location_records if r.get('changed')]
        total = len(location_records)
        
        return {
            'location': location,
            'total_records': total,
            'changed_records': len(changed),
            'change_rate': round(len(changed) / total * 100, 1) if total else 0,
            'suppliers': list(set(r.get('supplier') for r in location_records if r.get('supplier'))),
            'design_changes': sum(1 for r in changed if r.get('designChanged')),
            'supplier_changes': sum(1 for r in changed if r.get('supplierChanged')),
            'roj_changes': sum(1 for r in changed if r.get('scheduleChanged')),
            'forecast_delta': sum(r.get('qtyDelta', 0) for r in location_records),
            'high_risk_count': sum(1 for r in changed if r.get('riskLevel') in ['HIGH', 'CRITICAL']),
        }
    
    @staticmethod
    def compute_supplier_metrics(records: List[Dict], location: str, supplier: str) -> Dict[str, Any]:
        """Compute metrics for a specific supplier at a location."""
        location_records = [r for r in records if (r.get('locationId') or '').upper() == location.upper()]
        supplier_records = [r for r in location_records if (r.get('supplier') or '').upper() == supplier.upper()]
        
        if not supplier_records:
            return {'error': f'No records found for {supplier} at {location}'}
        
        changed = [r for r in supplier_records if r.get('changed')]
        
        return {
            'supplier': supplier,
            'location': location,
            'total_records': len(supplier_records),
            'changed_records': len(changed),
            'change_rate': round(len(changed) / len(supplier_records) * 100, 1) if supplier_records else 0,
            'design_changes': sum(1 for r in changed if r.get('designChanged')),
            'supplier_date_issues': sum(1 for r in changed if r.get('isSupplierDateMissing')),
            'roj_changes': sum(1 for r in changed if r.get('scheduleChanged')),
            'forecast_delta': sum(r.get('qtyDelta', 0) for r in supplier_records),
            'high_risk_count': sum(1 for r in changed if r.get('riskLevel') in ['HIGH', 'CRITICAL']),
        }
    
    @staticmethod
    def compute_comparison(records: List[Dict], entity1: str, entity2: str, scope_type: str) -> Dict[str, Any]:
        """Compute independent metrics for two entities."""
        
        def filter_by_entity(recs, entity, scope_type):
            if scope_type == 'location':
                return [r for r in recs if (r.get('locationId') or '').upper() == entity.upper()]
            elif scope_type == 'material_group':
                return [r for r in recs if (r.get('materialGroup') or '').upper() == entity.upper()]
            elif scope_type == 'material_id':
                return [r for r in recs if (r.get('materialId') or '').upper() == entity.upper()]
            return []
        
        def compute_entity_metrics(recs):
            if not recs:
                return {'total': 0, 'changed': 0, 'change_rate': 0}
            changed = [r for r in recs if r.get('changed')]
            return {
                'total': len(recs),
                'changed': len(changed),
                'change_rate': round(len(changed) / len(recs) * 100, 1),
                'design_changes': sum(1 for r in changed if r.get('designChanged')),
                'supplier_changes': sum(1 for r in changed if r.get('supplierChanged')),
                'roj_changes': sum(1 for r in changed if r.get('scheduleChanged')),
                'forecast_delta': sum(r.get('qtyDelta', 0) for r in recs),
            }
        
        recs1 = filter_by_entity(records, entity1, scope_type)
        recs2 = filter_by_entity(records, entity2, scope_type)
        
        return {
            'entity1': entity1,
            'entity2': entity2,
            'scope_type': scope_type,
            'metrics1': compute_entity_metrics(recs1),
            'metrics2': compute_entity_metrics(recs2),
        }


# ============================================================================
# STEP 4: DYNAMIC RESPONSE GENERATION
# ============================================================================

class ResponseGenerator:
    """Generate dynamic, reasoning-driven responses."""
    
    @staticmethod
    def generate_list_response(question: str, metrics: Dict[str, Any]) -> str:
        """Generate response for list queries."""
        if 'error' in metrics:
            return metrics['error']
        
        location = metrics.get('location', 'location')
        total = metrics.get('total_records', 0)
        changed = metrics.get('changed_records', 0)
        change_rate = metrics.get('change_rate', 0)
        suppliers = metrics.get('suppliers', [])
        
        # Direct answer
        answer = f"📊 {location}: {total} records total, {changed} changed ({change_rate}%)\n"
        
        # Supporting numbers
        if suppliers:
            answer += f"\n🏢 Suppliers ({len(suppliers)}):\n"
            for sup in sorted(suppliers)[:5]:
                answer += f"  • {sup}\n"
        
        # Key insight
        if change_rate > 50:
            answer += f"\n💡 Insight: High change rate ({change_rate}%) indicates significant planning volatility.\n"
        elif change_rate > 20:
            answer += f"\n💡 Insight: Moderate changes ({change_rate}%) suggest active planning adjustments.\n"
        else:
            answer += f"\n💡 Insight: Low change rate ({change_rate}%) indicates stable planning.\n"
        
        # Recommended action
        if change_rate > 50:
            answer += "✅ Action: Review high-change records for root causes."
        elif change_rate > 20:
            answer += "✅ Action: Monitor for emerging patterns."
        else:
            answer += "✅ Action: Continue current planning approach."
        
        return answer
    
    @staticmethod
    def generate_comparison_response(question: str, comparison: Dict[str, Any]) -> str:
        """Generate response for comparison queries."""
        entity1 = comparison['entity1']
        entity2 = comparison['entity2']
        m1 = comparison['metrics1']
        m2 = comparison['metrics2']
        
        if m1.get('total', 0) == 0 or m2.get('total', 0) == 0:
            return f"Cannot compare: insufficient data for {entity1} or {entity2}"
        
        # Direct answer
        answer = f"📊 Comparison: {entity1} vs {entity2}\n\n"
        
        # Supporting numbers
        answer += f"Metric                    {entity1:<15} {entity2:<15}\n"
        answer += "-" * 50 + "\n"
        answer += f"Total records             {m1['total']:<15} {m2['total']:<15}\n"
        answer += f"Changed                   {m1['changed']:<15} {m2['changed']:<15}\n"
        answer += f"Change rate               {m1['change_rate']:<14}% {m2['change_rate']:<14}%\n"
        answer += f"Design changes            {m1['design_changes']:<15} {m2['design_changes']:<15}\n"
        answer += f"Forecast delta            {m1['forecast_delta']:<15} {m2['forecast_delta']:<15}\n"
        
        # Key insight
        if m1['change_rate'] > m2['change_rate']:
            diff = m1['change_rate'] - m2['change_rate']
            answer += f"\n💡 Insight: {entity1} has {diff:.1f}% more changes than {entity2}.\n"
        elif m2['change_rate'] > m1['change_rate']:
            diff = m2['change_rate'] - m1['change_rate']
            answer += f"\n💡 Insight: {entity2} has {diff:.1f}% more changes than {entity1}.\n"
        else:
            answer += f"\n💡 Insight: Both have similar change rates.\n"
        
        # Recommended action
        higher = entity1 if m1['change_rate'] > m2['change_rate'] else entity2
        answer += f"✅ Action: Focus attention on {higher} for change management."
        
        return answer
    
    @staticmethod
    def generate_root_cause_response(question: str, metrics: Dict[str, Any]) -> str:
        """Generate response for root cause queries."""
        if 'error' in metrics:
            return metrics['error']
        
        location = metrics.get('location', 'location')
        changed = metrics.get('changed_records', 0)
        total = metrics.get('total_records', 0)
        design_changes = metrics.get('design_changes', 0)
        supplier_changes = metrics.get('supplier_changes', 0)
        roj_changes = metrics.get('roj_changes', 0)
        
        # Determine primary driver
        drivers = {
            'Design': design_changes,
            'Supplier': supplier_changes,
            'Schedule (ROJ)': roj_changes,
        }
        primary_driver = max(drivers, key=drivers.get) if any(drivers.values()) else 'None'
        
        # Direct answer
        answer = f"🔍 Root Cause Analysis: {location}\n\n"
        
        # What changed
        answer += f"What changed:\n"
        answer += f"  • Primary driver: {primary_driver}\n"
        answer += f"  • Records affected: {changed}/{total} ({round(changed/total*100, 1)}%)\n"
        
        # Why it matters
        answer += f"\nWhy it matters:\n"
        if changed == 0:
            answer += f"  • No changes detected - location is stable\n"
        elif round(changed/total*100, 1) > 50:
            answer += f"  • High change rate ({round(changed/total*100, 1)}%) indicates significant volatility\n"
        else:
            answer += f"  • Moderate changes ({round(changed/total*100, 1)}%) require monitoring\n"
        
        # Recommended action
        answer += f"\nRecommended action:\n"
        if primary_driver == 'Design':
            answer += f"  • Coordinate with engineering on design changes\n"
        elif primary_driver == 'Supplier':
            answer += f"  • Review supplier performance and reliability\n"
        elif primary_driver == 'Schedule (ROJ)':
            answer += f"  • Investigate ROJ delays and root causes\n"
        else:
            answer += f"  • Monitor for emerging patterns\n"
        
        return answer


# ============================================================================
# STEP 5: MAIN REASONING ENGINE
# ============================================================================

class ReasoningEngine:
    """Main orchestrator for query-aware reasoning."""
    
    def __init__(self):
        self.extractor = EntityExtractor()
        self.classifier = IntentClassifier()
        self.computation = ScopedComputation()
        self.generator = ResponseGenerator()
    
    def process_query(self, question: str, detail_records: List[Dict]) -> str:
        """
        Process query through strict pipeline:
        1. Extract entities
        2. Classify intent
        3. Compute scoped metrics
        4. Generate dynamic response
        """
        logger.info(f"Processing query: {question}")
        
        # Step 1: Extract entities
        location = self.extractor.extract_location(question)
        material_id = self.extractor.extract_material_id(question)
        material_group = self.extractor.extract_material_group(question)
        supplier = self.extractor.extract_supplier(question)
        comparison_pair = self.extractor.extract_comparison_pair(question)
        
        logger.info(f"Extracted: location={location}, material_id={material_id}, "
                   f"material_group={material_group}, supplier={supplier}, comparison={comparison_pair}")
        
        # Step 2: Classify intent
        intent = self.classifier.classify(question)
        logger.info(f"Intent: {intent}")
        
        # Step 3: Route to computation based on intent + entities
        if intent == 'compare' and comparison_pair:
            entity1, entity2 = comparison_pair
            # Determine scope type from entities
            if location and not material_id and not material_group:
                scope_type = 'location'
            elif material_id:
                scope_type = 'material_id'
            else:
                scope_type = 'material_group'
            
            metrics = self.computation.compute_comparison(detail_records, entity1, entity2, scope_type)
            return self.generator.generate_comparison_response(question, metrics)
        
        elif intent == 'list' and location:
            metrics = self.computation.compute_location_metrics(detail_records, location)
            return self.generator.generate_list_response(question, metrics)
        
        elif intent == 'root_cause' and location:
            metrics = self.computation.compute_location_metrics(detail_records, location)
            return self.generator.generate_root_cause_response(question, metrics)
        
        else:
            # For queries without specific scope, provide global analysis
            # This handles: "Which supplier has the most impact?", "Which material groups changed the most?", etc.
            logger.info(f"No specific scope detected. Providing global analysis for intent: {intent}")
            
            # Compute global metrics
            if not detail_records:
                return "No data available to analyze."
            
            # Count changes
            total_records = len(detail_records)
            changed_records = sum(1 for r in detail_records if r.get('changed', False))
            change_rate = round(changed_records / max(total_records, 1) * 100, 1)
            
            # Provide a meaningful response based on intent
            if intent == 'list':
                # Global list query - show top suppliers/materials/locations
                return self._generate_global_list_response(question, detail_records, total_records, changed_records, change_rate)
            elif intent == 'root_cause':
                # Global root cause - show overall drivers
                return self._generate_global_root_cause_response(question, detail_records, total_records, changed_records, change_rate)
            elif intent == 'summary':
                # Global summary
                return self._generate_global_summary_response(question, detail_records, total_records, changed_records, change_rate)
            else:
                # Default: provide global metrics
                return self._generate_global_metrics_response(question, detail_records, total_records, changed_records, change_rate)
    def _generate_global_list_response(self, question: str, detail_records: List[Dict], total: int, changed: int, change_rate: float) -> str:
        """Generate response for global list queries (e.g., 'Which supplier has the most impact?')."""
        # Analyze by supplier
        supplier_stats = {}
        for record in detail_records:
            supplier = record.get('supplierId', 'Unknown')
            if supplier not in supplier_stats:
                supplier_stats[supplier] = {'total': 0, 'changed': 0}
            supplier_stats[supplier]['total'] += 1
            if record.get('changed', False):
                supplier_stats[supplier]['changed'] += 1
        
        # Sort by impact (changed records)
        top_suppliers = sorted(supplier_stats.items(), key=lambda x: x[1]['changed'], reverse=True)[:5]
        
        response = f"📊 Global Analysis: {total} records total, {changed} changed ({change_rate}%)\n\n"
        response += "🏢 Top Suppliers by Impact:\n"
        for supplier, stats in top_suppliers:
            rate = round(stats['changed'] / max(stats['total'], 1) * 100, 1)
            response += f"  • {supplier}: {stats['changed']} changes ({rate}%)\n"
        
        response += f"\n💡 Insight: Overall change rate is {change_rate}%.\n"
        response += "✅ Action: Review top suppliers for planning adjustments."
        return response
    
    def _generate_global_root_cause_response(self, question: str, detail_records: List[Dict], total: int, changed: int, change_rate: float) -> str:
        """Generate response for global root cause queries."""
        # Analyze change drivers
        drivers = {'quantity': 0, 'design': 0, 'schedule': 0, 'other': 0}
        for record in detail_records:
            if record.get('changed', False):
                if record.get('quantityChanged'):
                    drivers['quantity'] += 1
                if record.get('designChanged'):
                    drivers['design'] += 1
                if record.get('scheduleChanged'):
                    drivers['schedule'] += 1
                if not any([record.get('quantityChanged'), record.get('designChanged'), record.get('scheduleChanged')]):
                    drivers['other'] += 1
        
        # Find primary driver
        primary_driver = max(drivers, key=drivers.get)
        
        response = f"🔍 Root Cause Analysis: Global\n\n"
        response += f"What changed:\n"
        response += f"  • Primary driver: {primary_driver}\n"
        response += f"  • Records affected: {changed}/{total} ({change_rate}%)\n\n"
        response += f"Why it matters:\n"
        response += f"  • {primary_driver.capitalize()} changes are the main driver\n"
        response += f"  • Affects {change_rate}% of planning records\n\n"
        response += f"Recommended action:\n"
        response += f"  • Focus on {primary_driver} management\n"
        response += f"  • Review supplier performance\n"
        response += f"  • Monitor for escalation"
        return response
    
    def _generate_global_summary_response(self, question: str, detail_records: List[Dict], total: int, changed: int, change_rate: float) -> str:
        """Generate response for global summary queries."""
        # Count by location
        locations = set(r.get('locationId') for r in detail_records if r.get('locationId'))
        
        response = f"📊 Planning Health Summary\n\n"
        response += f"Overall Metrics:\n"
        response += f"  • Total Records: {total:,}\n"
        response += f"  • Changed Records: {changed:,}\n"
        response += f"  • Change Rate: {change_rate}%\n"
        response += f"  • Locations: {len(locations)}\n\n"
        response += f"Status: {'🔴 CRITICAL' if change_rate > 50 else '🟡 HIGH' if change_rate > 25 else '🟢 NORMAL'}\n\n"
        response += f"Action: Review planning adjustments needed."
        return response
    
    def _generate_global_metrics_response(self, question: str, detail_records: List[Dict], total: int, changed: int, change_rate: float) -> str:
        """Generate response for default global queries."""
        response = f"📊 Global Metrics\n\n"
        response += f"Total Records: {total:,}\n"
        response += f"Changed: {changed:,}\n"
        response += f"Change Rate: {change_rate}%\n\n"
        response += f"💡 Insight: {change_rate}% of records have changes.\n"
        response += f"✅ Action: Review planning adjustments."
        return response
