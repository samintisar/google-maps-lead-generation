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
        
        # Build comprehensive query with system instructions
        search_query = f"""
        You are a business intelligence researcher. Provide detailed, accurate, and up-to-date information about companies and their business context. Focus on actionable insights for sales and business development.
        
        Research the following business and provide detailed insights:
        
        {' | '.join(query_parts)}
        
        Please provide comprehensive information about {company_name} including:
        
        1. SOCIAL MEDIA PROFILES:
           - LinkedIn company page URL
           - Twitter/X profile URL
           - Facebook business page URL
           - Instagram business profile URL
        
        2. IDEAL CUSTOMER PROFILE (ICP):
           - Detailed description of their target customers
           - Customer demographics and firmographics
           - Industries they typically serve
           - Company size they target
        
        3. PAIN POINTS:
           - Current business challenges they face
           - Industry-specific problems
           - Operational difficulties
           - Market pressures
        
        4. KEY BUSINESS GOALS:
           - Current strategic objectives
           - Growth targets
           - Market expansion plans
           - Digital transformation initiatives
        
        5. COMPANY OVERVIEW:
           - Business model and value proposition
           - Core products and services
           - Market position and competitive advantages
           - Company culture and values
        
        6. RECENT NEWS & UPDATES:
           - Recent press releases
           - Funding announcements
           - Product launches
           - Strategic partnerships
           - Leadership changes
        
        7. KEY PERSONNEL:
           - CEO/Founder information
           - Key decision makers
           - Department heads
           - Contact information if publicly available
        
        Please provide specific, actionable insights that would be valuable for sales outreach and relationship building.
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
                    "role": "user",
                    "content": query
                }
            ]
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
            
            # Initialize structured data
            structured_data = {
                "linkedin_profile": None,
                "twitter_profile": None,
                "facebook_profile": None,
                "instagram_profile": None,
                "ideal_customer_profile": None,
                "pain_points": None,
                "key_goals": None,
                "company_description": None,
                "recent_news": None,
                "key_personnel": [],
                "enrichment_confidence": 0.0,
                "raw_response": content,
                "citations": citations,
                "enriched_at": datetime.utcnow().isoformat()
            }
            
            # Extract social media profiles using keyword matching
            structured_data.update(self._extract_social_profiles(content))
            
            # Extract business intelligence
            structured_data.update(self._extract_business_intelligence(content))
            
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
                "ideal_customer_profile": None,
                "pain_points": None,
                "key_goals": None,
                "company_description": None,
                "recent_news": None,
                "key_personnel": [],
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
    
    def _extract_business_intelligence(self, content: str) -> Dict[str, Any]:
        """Extract business intelligence from content using section parsing."""
        
        intelligence = {
            "ideal_customer_profile": None,
            "pain_points": None,
            "key_goals": None,
            "company_description": None,
            "recent_news": None,
            "key_personnel": []
        }
        
        # Split content into sections
        sections = content.split('\n\n')
        
        for section in sections:
            section_lower = section.lower()
            
            # ICP extraction
            if any(keyword in section_lower for keyword in ['ideal customer', 'target customer', 'customer profile', 'icp']):
                intelligence["ideal_customer_profile"] = section.strip()
            
            # Pain points extraction
            elif any(keyword in section_lower for keyword in ['pain point', 'challenge', 'problem', 'difficulty']):
                intelligence["pain_points"] = section.strip()
            
            # Goals extraction
            elif any(keyword in section_lower for keyword in ['goal', 'objective', 'strategy', 'plan', 'target']):
                intelligence["key_goals"] = section.strip()
            
            # Company description extraction
            elif any(keyword in section_lower for keyword in ['company overview', 'business model', 'about', 'description']):
                intelligence["company_description"] = section.strip()
            
            # Recent news extraction
            elif any(keyword in section_lower for keyword in ['recent', 'news', 'announcement', 'update', 'press release']):
                intelligence["recent_news"] = section.strip()
            
            # Key personnel extraction
            elif any(keyword in section_lower for keyword in ['personnel', 'team', 'leadership', 'executive', 'ceo', 'founder']):
                # For now, store as text - could be enhanced to parse individual people
                if section.strip():
                    intelligence["key_personnel"] = [{"role": "Leadership Team", "info": section.strip()}]
        
        return intelligence
    
    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on amount of data enriched."""
        
        score = 0.0
        max_score = 10.0
        
        # Social profiles (2 points each, max 8)
        social_fields = ["linkedin_profile", "twitter_profile", "facebook_profile", "instagram_profile"]
        for field in social_fields:
            if data.get(field):
                score += 2.0
        
        # Business intelligence (0.5 points each, max 2)
        business_fields = ["ideal_customer_profile", "pain_points", "key_goals", "company_description"]
        for field in business_fields:
            if data.get(field):
                score += 0.5
        
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