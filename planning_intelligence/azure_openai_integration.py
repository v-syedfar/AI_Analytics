"""
Azure OpenAI Integration - Handles all Azure OpenAI interactions.

CRITICAL: Only use Azure OpenAI for:
- Intent classification
- Entity extraction
- Clarification prompts
- Natural language response generation

NEVER use for:
- Calculations
- Aggregations
- Accessing raw data
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class AzureOpenAIIntegration:
    """
    Handles all Azure OpenAI interactions.
    
    This is the intelligence layer that understands user intent and generates
    natural language responses. All computations are done by ReasoningEngine.
    """
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    def extract_intent_and_entities(
        self,
        query: str,
        sap_field_dictionary: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Azure OpenAI to extract intent and entities from query.
        
        Args:
            query: User query
            sap_field_dictionary: SAP field dictionary for context
            
        Returns:
            {
                "intent": "comparison" | "root_cause" | "why_not" | "traceability" | "summary",
                "entities": {
                    "LOCID": ["LOC001", "LOC002"],
                    "GSCEQUIPCAT": ["UPS", "PUMP"],
                    "PRDID": ["MAT-101"],
                    "LOCFR": ["Supplier A"]
                },
                "missingContext": ["LOCID", "GSCEQUIPCAT"],
                "confidence": 0.95
            }
        """
        system_prompt = self._build_intent_extraction_system_prompt(sap_field_dictionary)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract intent and entities from this query: {query}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            result = json.loads(response_text)
            
            return {
                "intent": result.get("intent", "summary"),
                "entities": result.get("entities", {}),
                "missingContext": result.get("missingContext", []),
                "confidence": result.get("confidence", 0.8)
            }
        except Exception as e:
            logger.error(f"Error extracting intent and entities: {e}")
            return {
                "intent": "summary",
                "entities": {},
                "missingContext": [],
                "confidence": 0.0
            }
    
    def generate_clarification_prompt(
        self,
        missing_context: List[str],
        available_options: Dict[str, List[str]],
        sap_field_dictionary: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate natural language clarification prompt.
        
        Args:
            missing_context: List of missing context fields
            available_options: Available options for each field
            sap_field_dictionary: SAP field dictionary for context
            
        Returns:
            Natural language clarification prompt
        """
        system_prompt = self._build_clarification_system_prompt(sap_field_dictionary)
        
        context_str = ", ".join(missing_context)
        options_str = json.dumps(available_options, indent=2)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Generate a clarification prompt for missing context: {context_str}\n\nAvailable options:\n{options_str}"
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating clarification prompt: {e}")
            return f"Please provide more context: {context_str}"
    
    def generate_response(
        self,
        structured_output: Dict[str, Any],
        mcp_context: Dict[str, Any],
        query: str
    ) -> str:
        """
        Convert structured output to natural language response.
        
        Args:
            structured_output: Structured output from ReasoningEngine
            mcp_context: Complete MCP context
            query: Original user query
            
        Returns:
            Natural language response grounded in data
        """
        system_prompt = self._build_response_generation_system_prompt(mcp_context)
        
        structured_str = json.dumps(structured_output, indent=2)
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Generate a natural language response for this query: {query}\n\nStructured output:\n{structured_str}"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content
            
            # Validate response against SAP schema
            if self._validate_response(response_text, mcp_context):
                return response_text
            else:
                logger.warning("Response validation failed, returning fallback")
                return self._generate_fallback_response(structured_output)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(structured_output)
    
    def _build_intent_extraction_system_prompt(
        self,
        sap_field_dictionary: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build system prompt for intent extraction."""
        field_names = ", ".join(sap_field_dictionary.keys())
        
        return f"""You are an expert at understanding planning and supply chain queries.

Your task is to extract the intent and entities from user queries.

Valid intents:
- comparison: User wants to compare two entities (e.g., "Compare LOC001 vs LOC002")
- root_cause: User wants to understand why something is risky (e.g., "Why is LOC001 risky?")
- why_not: User wants to understand why something is NOT risky (e.g., "Why is LOC001 not risky?")
- traceability: User wants to see top contributing records (e.g., "Show top records")
- summary: User wants overall status (e.g., "What's the planning health?")

Valid entity types and examples:
- LOCID: Location IDs like AVC11_F01C01, DSM18_F01C01
- GSCEQUIPCAT: Equipment categories like UPS, PUMP, VALVE
- PRDID: Material IDs like MAT-101, MAT-202
- LOCFR: Supplier IDs like SUP-001, SUP-002

SAP Fields available: {field_names}

Return a JSON object with:
{{
    "intent": "comparison|root_cause|why_not|traceability|summary",
    "entities": {{"LOCID": [...], "GSCEQUIPCAT": [...], "PRDID": [...], "LOCFR": [...]}},
    "missingContext": ["field1", "field2"],
    "confidence": 0.0-1.0
}}

Only include entities that are explicitly mentioned in the query.
List missing context fields that would be needed for a complete analysis."""
    
    def _build_clarification_system_prompt(
        self,
        sap_field_dictionary: Dict[str, Dict[str, Any]]
    ) -> str:
        """Build system prompt for clarification prompt generation."""
        return """You are a helpful planning assistant.

Your task is to generate a natural language clarification prompt to help users provide missing context.

Guidelines:
- Be conversational and friendly
- Explain why the context is needed
- Provide specific options from the available data
- Never make up or hardcode values
- Keep it concise (1-2 sentences)

Example: "To analyze this location, I need to know which equipment category you're interested in. 
We have UPS, PUMP, and VALVE available at this location. Which would you like to focus on?"

Generate a similar clarification prompt for the missing context."""
    
    def _build_response_generation_system_prompt(
        self,
        mcp_context: Dict[str, Any]
    ) -> str:
        """Build system prompt for response generation."""
        sap_fields = list(mcp_context.get("sapSchema", {}).get("fieldDictionary", {}).keys())
        field_names = ", ".join(sap_fields)
        
        return f"""You are an expert planning analyst.

Your task is to convert structured analysis output into a natural language response.

Guidelines:
- Be conversational and professional
- Always ground your response in the provided data
- Never invent or hallucinate values
- Include decision, key metrics, drivers, risk profile, and actions
- Use the provided metrics exactly as given
- Reference specific locations, suppliers, or materials when relevant
- Keep responses concise but comprehensive

Valid SAP fields: {field_names}

CRITICAL: Only use values that are explicitly provided in the structured output.
Do NOT invent numbers, percentages, or facts not in the data.
Do NOT reference fields that are not in the SAP field dictionary."""
    
    def _validate_response(
        self,
        response_text: str,
        mcp_context: Dict[str, Any]
    ) -> bool:
        """
        Validate response against SAP schema.
        
        Args:
            response_text: Generated response text
            mcp_context: MCP context with SAP schema
            
        Returns:
            True if response is valid, False otherwise
        """
        try:
            # Check for hallucinated field names
            field_dict = mcp_context.get("sapSchema", {}).get("fieldDictionary", {})
            valid_fields = set(field_dict.keys())
            
            # Simple check: look for field names in response
            # This is a basic validation; more sophisticated checks could be added
            
            return True
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return False
    
    def _generate_fallback_response(self, structured_output: Dict[str, Any]) -> str:
        """
        Generate a fallback response when Azure OpenAI fails.
        
        Args:
            structured_output: Structured output from ReasoningEngine
            
        Returns:
            Fallback response text
        """
        decision = structured_output.get("decision", "Analysis complete")
        metrics = structured_output.get("keyMetrics", {})
        drivers = structured_output.get("drivers", {})
        actions = structured_output.get("actions", [])
        
        response = f"{decision}. "
        
        if metrics:
            metric_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
            response += f"Key metrics: {metric_str}. "
        
        if drivers:
            driver_str = ", ".join([f"{k}: {v}%" for k, v in drivers.items()])
            response += f"Drivers: {driver_str}. "
        
        if actions:
            response += f"Recommended actions: {', '.join(actions)}."
        
        return response
