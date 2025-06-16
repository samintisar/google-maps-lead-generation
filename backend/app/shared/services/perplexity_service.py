"""
Perplexity API service for lead enrichment.
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime

from ...domains.lead_management.models import Lead


class PerplexityEnrichmentService:
    """Service for enriching lead data using Perplexity API."""
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.model = "llama-3.1-sonar-large-128k-online"  # Using the model from reference
        
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
    
    async def enrich_lead(self, lead: Lead) -> Dict[str, Any]:
        """
        Enrich a lead with comprehensive business intelligence.
        
        Args:
            lead: Lead object to enrich
            
        Returns:
            Dict containing enrichment data
        """
        
        # Prepare search query based on available lead information
        search_query = self._build_search_query(lead)
        
        # Get enrichment data from Perplexity
        enrichment_data = await self._get_enrichment_data(search_query)
        
        # Parse and structure the response
        structured_data = self._parse_enrichment_response(enrichment_data)
        
        return structured_data
    
    def _build_search_query(self, lead: Lead) -> str:
        """Build a comprehensive search query for the lead."""
        
        query_parts = []
        
        # Company information
        if lead.company:
            query_parts.append(f"Company: {lead.company}")
        
        # Industry context
        if lead.industry:
            query_parts.append(f"Industry: {lead.industry}")
        
        # Location context
        if lead.address:
            query_parts.append(f"Location: {lead.address}")
        
        # Website context
        if lead.website:
            query_parts.append(f"Website: {lead.website}")
        
        # Contact information
        if lead.name:
            query_parts.append(f"Contact: {lead.name}")
        
        company_name = lead.company or "the company"
        
        # Build comprehensive query with system instructions for JSON output
        search_query = f"""
        You are a business intelligence researcher. Research the following business and provide detailed insights in STRICT JSON format.

        Business to research:
        {' | '.join(query_parts)}

        Please respond with ONLY a valid JSON object containing exactly these 6 fields for {company_name}:

        {{
            "company_description": "Brief overview of the business model, value proposition, core products/services, and market position (2-3 sentences)",
            "ideal_customer_profile": "Detailed description of their target customers, demographics, company sizes they serve, and industries they focus on (2-3 sentences)",
            "pain_points": "Current business challenges, industry problems, operational difficulties, and market pressures they face (2-3 sentences)",
            "key_goals": "Strategic objectives, growth targets, market expansion plans, and key business initiatives (2-3 sentences)",
            "recent_news": "Recent company news, press releases, funding, product launches, or strategic partnerships. If none found, state 'No recent news found' (1-2 sentences)",
            "key_personnel": "Key decision makers, CEO/founder info, department heads, or contact information if publicly available. If limited info, state 'Limited personnel information available' (1-2 sentences)"
        }}

        CRITICAL REQUIREMENTS:
        - Respond with ONLY valid JSON - no additional text before or after
        - Each field must be a simple string (no arrays or nested objects)
        - Keep responses concise but informative (1-3 sentences per field)
        - If information is not available for a field, state that clearly
        - Do not include social media URLs in these fields
        - Focus on actionable business intelligence for sales outreach
        """
        
        return search_query.strip()
    
    async def _get_enrichment_data(self, query: str) -> Dict[str, Any]:
        """Make API call to Perplexity to get enrichment data."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a business intelligence researcher. Always respond with valid JSON only. No additional text or formatting."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.2,  # Lower temperature for more consistent JSON output
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        raise Exception(f"Perplexity API error: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            raise Exception("Perplexity API request timed out")
        except Exception as e:
            raise Exception(f"Failed to call Perplexity API: {str(e)}")
    
    def _parse_enrichment_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and structure the Perplexity API response."""
        
        try:
            # Extract the main content
            content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = api_response.get("citations", [])
            
            # Initialize structured data with defaults
            structured_data = {
                "linkedin_profile": None,
                "twitter_profile": None,
                "facebook_profile": None,
                "instagram_profile": None,
                "ideal_customer_profile": "No customer profile information available",
                "pain_points": "No pain points identified",
                "key_goals": "No key goals identified",
                "company_description": "No company description available",
                "recent_news": "No recent news found",
                "key_personnel": "No personnel information available",
                "enrichment_confidence": 0.0,
                "raw_response": content,
                "citations": citations,
                "enriched_at": datetime.utcnow().isoformat()
            }
            
            # Try to parse JSON from the response
            try:
                # Clean the content - remove any markdown formatting
                cleaned_content = content.strip()
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                # Parse the JSON
                parsed_data = json.loads(cleaned_content)
                
                # Update structured data with parsed JSON
                if isinstance(parsed_data, dict):
                    for key in ["company_description", "ideal_customer_profile", "pain_points", 
                               "key_goals", "recent_news", "key_personnel"]:
                        if key in parsed_data and parsed_data[key]:
                            structured_data[key] = str(parsed_data[key]).strip()
                
            except json.JSONDecodeError as e:
                # Fallback to text parsing if JSON fails
                print(f"JSON parsing failed: {e}. Falling back to text extraction.")
                structured_data.update(self._extract_business_intelligence_fallback(content))
            
            # Extract social media profiles from the raw content
            structured_data.update(self._extract_social_profiles(content))
            
            # Calculate confidence score based on amount of data found
            structured_data["enrichment_confidence"] = self._calculate_confidence_score(structured_data)
            
            return structured_data
            
        except Exception as e:
            # Return minimal structure with error info
            return {
                "linkedin_profile": None,
                "twitter_profile": None,
                "facebook_profile": None,
                "instagram_profile": None,
                "ideal_customer_profile": "Error occurred during enrichment",
                "pain_points": "Error occurred during enrichment",
                "key_goals": "Error occurred during enrichment",
                "company_description": "Error occurred during enrichment",
                "recent_news": "Error occurred during enrichment",
                "key_personnel": "Error occurred during enrichment",
                "enrichment_confidence": 0.0,
                "error": str(e),
                "enriched_at": datetime.utcnow().isoformat()
            }
    
    def _extract_social_profiles(self, content: str) -> Dict[str, str]:
        """Extract social media profile URLs from content."""
        
        profiles = {
            "linkedin_profile": None,
            "twitter_profile": None,
            "facebook_profile": None,
            "instagram_profile": None
        }
        
        # Simple regex patterns for common social media URLs
        import re
        
        # LinkedIn patterns
        linkedin_patterns = [
            r'linkedin\.com/company/([^/\s]+)',
            r'linkedin\.com/in/([^/\s]+)',
            r'https?://[^/]*linkedin\.com/[^\s]+',
        ]
        
        # Twitter patterns
        twitter_patterns = [
            r'twitter\.com/([^/\s]+)',
            r'x\.com/([^/\s]+)',
            r'https?://[^/]*twitter\.com/[^\s]+',
            r'https?://[^/]*x\.com/[^\s]+',
        ]
        
        # Facebook patterns
        facebook_patterns = [
            r'facebook\.com/([^/\s]+)',
            r'https?://[^/]*facebook\.com/[^\s]+',
        ]
        
        # Instagram patterns
        instagram_patterns = [
            r'instagram\.com/([^/\s]+)',
            r'https?://[^/]*instagram\.com/[^\s]+',
        ]
        
        # Extract LinkedIn
        for pattern in linkedin_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                profiles["linkedin_profile"] = match.group(0) if match.group(0).startswith('http') else f"https://linkedin.com/company/{match.group(1)}"
                break
        
        # Extract Twitter
        for pattern in twitter_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                profiles["twitter_profile"] = match.group(0) if match.group(0).startswith('http') else f"https://twitter.com/{match.group(1)}"
                break
        
        # Extract Facebook
        for pattern in facebook_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                profiles["facebook_profile"] = match.group(0) if match.group(0).startswith('http') else f"https://facebook.com/{match.group(1)}"
                break
        
        # Extract Instagram
        for pattern in instagram_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                profiles["instagram_profile"] = match.group(0) if match.group(0).startswith('http') else f"https://instagram.com/{match.group(1)}"
                break
        
        return profiles
    
    def _extract_business_intelligence_fallback(self, content: str) -> Dict[str, Any]:
        """Fallback method to extract business intelligence from unstructured content."""
        
        intelligence = {
            "ideal_customer_profile": "No customer profile information available",
            "pain_points": "No pain points identified",
            "key_goals": "No key goals identified", 
            "company_description": "No company description available",
            "recent_news": "No recent news found",
            "key_personnel": "No personnel information available"
        }
        
        # Split content into sections and look for relevant information
        sections = content.split('\n')
        current_section = ""
        
        for line in sections:
            line_lower = line.lower().strip()
            
            # Skip empty lines
            if not line_lower:
                continue
                
            # Look for section headers or content patterns
            if any(keyword in line_lower for keyword in ['customer profile', 'ideal customer', 'target customer', 'icp']):
                current_section = "ideal_customer_profile"
                continue
            elif any(keyword in line_lower for keyword in ['pain point', 'challenge', 'problem', 'difficulty']):
                current_section = "pain_points"
                continue
            elif any(keyword in line_lower for keyword in ['goal', 'objective', 'strategy', 'plan']):
                current_section = "key_goals"
                continue
            elif any(keyword in line_lower for keyword in ['company', 'business model', 'overview', 'description']):
                current_section = "company_description"
                continue
            elif any(keyword in line_lower for keyword in ['recent', 'news', 'announcement', 'update']):
                current_section = "recent_news"
                continue
            elif any(keyword in line_lower for keyword in ['personnel', 'team', 'leadership', 'ceo', 'founder']):
                current_section = "key_personnel"
                continue
            
            # Add content to current section if we have one
            if current_section and line.strip() and not line.startswith('#'):
                if intelligence[current_section] in ["No customer profile information available", 
                                                    "No pain points identified", 
                                                    "No key goals identified",
                                                    "No company description available",
                                                    "No recent news found",
                                                    "No personnel information available"]:
                    intelligence[current_section] = line.strip()
                else:
                    intelligence[current_section] += " " + line.strip()
        
        # Clean up the extracted text
        for key in intelligence:
            if intelligence[key] and len(intelligence[key]) > 500:
                intelligence[key] = intelligence[key][:500] + "..."
        
        return intelligence
    
    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on amount of data enriched."""
        
        score = 0.0
        max_score = 10.0
        
        # Social profiles (1 point each, max 4)
        social_fields = ["linkedin_profile", "twitter_profile", "facebook_profile", "instagram_profile"]
        for field in social_fields:
            if data.get(field):
                score += 1.0
        
        # Business intelligence (1 point each, max 6)
        business_fields = ["ideal_customer_profile", "pain_points", "key_goals", 
                          "company_description", "recent_news", "key_personnel"]
        for field in business_fields:
            field_value = data.get(field)
            # Only count if we have actual data (not default messages)
            if (field_value and 
                field_value not in ["No customer profile information available", 
                                   "No pain points identified", 
                                   "No key goals identified",
                                   "No company description available",
                                   "No recent news found",
                                   "No personnel information available",
                                   "Error occurred during enrichment"]):
                score += 1.0
        
        # Normalize to 0-1 scale
        return min(score / max_score, 1.0)
    
    async def enrich_multiple_leads(self, leads: List[Lead]) -> List[Dict[str, Any]]:
        """Enrich multiple leads concurrently."""
        
        tasks = [self.enrich_lead(lead) for lead in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        enriched_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                enriched_results.append({
                    "lead_id": leads[i].id,
                    "error": str(result),
                    "enrichment_confidence": 0.0,
                    "enriched_at": datetime.utcnow().isoformat()
                })
            else:
                result["lead_id"] = leads[i].id
                enriched_results.append(result)
        
        return enriched_results 