"""
Lead Enrichment Service - Comprehensive lead data enrichment and normalization.
Implements data cleaning, normalization, and augmentation with external data sources.
"""
import logging
import re
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

import requests
from email_validator import validate_email, EmailNotValidError

from models import Lead, ActivityLog, Integration, Organization
from utils.error_handling import with_retry, handle_n8n_exception

logger = logging.getLogger(__name__)

class LeadEnrichmentService:
    """
    Comprehensive lead enrichment service for data cleaning, normalization, and augmentation.
    """
    
    def __init__(self, db: Session):
        """Initialize the lead enrichment service."""
        self.db = db
        self.timeout = 10  # Default timeout for external API calls
        
        # Email patterns for domain extraction
        self.email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Company name cleaning patterns
        self.company_suffixes = [
            'inc', 'inc.', 'corp', 'corp.', 'corporation', 'llc', 'ltd', 'ltd.',
            'limited', 'co', 'co.', 'company', 'enterprises', 'group', 'holdings',
            'partners', 'associates', 'solutions', 'services', 'technologies', 'tech'
        ]
        
        # Industry classification mapping
        self.industry_keywords = {
            'technology': ['software', 'tech', 'saas', 'app', 'digital', 'ai', 'ml', 'data'],
            'healthcare': ['health', 'medical', 'hospital', 'pharma', 'biotech', 'clinic'],
            'finance': ['bank', 'finance', 'investment', 'insurance', 'fintech', 'trading'],
            'retail': ['retail', 'ecommerce', 'e-commerce', 'shopping', 'store', 'marketplace'],
            'manufacturing': ['manufacturing', 'factory', 'industrial', 'production', 'assembly'],
            'consulting': ['consulting', 'advisory', 'strategy', 'management', 'professional'],
            'education': ['education', 'school', 'university', 'learning', 'training', 'academy'],
            'real_estate': ['real estate', 'property', 'housing', 'development', 'construction'],
            'marketing': ['marketing', 'advertising', 'agency', 'creative', 'branding', 'media'],
            'legal': ['legal', 'law', 'attorney', 'lawyer', 'firm', 'judicial']
        }
    
    async def enrich_lead(self, lead_id: int, enrichment_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Comprehensive lead enrichment with multiple data sources and techniques.
        
        Args:
            lead_id: ID of the lead to enrich
            enrichment_types: Specific types of enrichment to perform
                            (email, phone, company, social, dedup, normalize)
        
        Returns:
            Dict containing enrichment results and metadata
        """
        try:
            lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                raise ValueError(f"Lead {lead_id} not found")
            
            # Default enrichment types
            if enrichment_types is None:
                enrichment_types = ['email', 'phone', 'company', 'normalize', 'dedup']
            
            enrichment_results = {
                "lead_id": lead_id,
                "enrichment_types": enrichment_types,
                "original_data": self._get_lead_snapshot(lead),
                "enriched_data": {},
                "data_sources": [],
                "validation_results": {},
                "errors": [],
                "metadata": {
                    "enriched_at": datetime.utcnow().isoformat(),
                    "processing_time_ms": 0
                }
            }
            
            start_time = datetime.utcnow()
            
            # Email enrichment and validation
            if 'email' in enrichment_types:
                email_result = await self._enrich_email(lead)
                enrichment_results["enriched_data"]["email"] = email_result
                enrichment_results["validation_results"]["email"] = email_result.get("validation", {})
                if email_result.get("errors"):
                    enrichment_results["errors"].extend(email_result["errors"])
            
            # Phone number validation and formatting
            if 'phone' in enrichment_types:
                phone_result = await self._enrich_phone(lead)
                enrichment_results["enriched_data"]["phone"] = phone_result
                enrichment_results["validation_results"]["phone"] = phone_result.get("validation", {})
                if phone_result.get("errors"):
                    enrichment_results["errors"].extend(phone_result["errors"])
            
            # Company enrichment
            if 'company' in enrichment_types:
                company_result = await self._enrich_company(lead)
                enrichment_results["enriched_data"]["company"] = company_result
                enrichment_results["data_sources"].extend(company_result.get("sources", []))
                if company_result.get("errors"):
                    enrichment_results["errors"].extend(company_result["errors"])
            
            # Social media enrichment
            if 'social' in enrichment_types:
                social_result = await self._enrich_social_profiles(lead)
                enrichment_results["enriched_data"]["social"] = social_result
                enrichment_results["data_sources"].extend(social_result.get("sources", []))
                if social_result.get("errors"):
                    enrichment_results["errors"].extend(social_result["errors"])
            
            # Data normalization
            if 'normalize' in enrichment_types:
                normalization_result = await self._normalize_lead_data(lead)
                enrichment_results["enriched_data"]["normalization"] = normalization_result
                if normalization_result.get("errors"):
                    enrichment_results["errors"].extend(normalization_result["errors"])
            
            # Deduplication check
            if 'dedup' in enrichment_types:
                dedup_result = await self._check_duplicates(lead)
                enrichment_results["enriched_data"]["deduplication"] = dedup_result
                if dedup_result.get("errors"):
                    enrichment_results["errors"].extend(dedup_result["errors"])
            
            # Apply enriched data to lead
            await self._apply_enrichment_to_lead(lead, enrichment_results)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            enrichment_results["metadata"]["processing_time_ms"] = processing_time
            
            # Log enrichment activity
            await self._log_enrichment_activity(lead_id, enrichment_results)
            
            logger.info(f"Enrichment completed for lead {lead_id} in {processing_time:.2f}ms")
            
            return enrichment_results
            
        except Exception as e:
            logger.error(f"Failed to enrich lead {lead_id}: {e}")
            raise
    
    async def _enrich_email(self, lead: Lead) -> Dict[str, Any]:
        """Validate and enrich email data."""
        result = {
            "original_email": lead.email,
            "validation": {},
            "domain_info": {},
            "reputation": {},
            "errors": []
        }
        
        try:
            if not lead.email:
                result["errors"].append("No email address provided")
                return result
            
            # Email validation
            try:
                # Configure email validator with more permissive settings
                valid = validate_email(
                    lead.email,
                    check_deliverability=False  # Don't check actual deliverability to avoid network issues
                )
                result["validation"] = {
                    "is_valid": True,
                    "normalized_email": valid.email,
                    "domain": valid.domain,
                    "local_part": valid.local,
                    "ascii_email": valid.ascii_email,
                    "ascii_domain": valid.ascii_domain
                }
                
                # Extract domain information
                domain = valid.domain
                result["domain_info"] = await self._get_domain_info(domain)
                
            except EmailNotValidError as e:
                result["validation"] = {
                    "is_valid": False,
                    "error": str(e),
                    "error_code": e.code if hasattr(e, 'code') else 'unknown'
                }
                result["errors"].append(f"Email validation failed: {e}")
                
                # For test environments, try basic regex validation as fallback
                if self._is_valid_email_format(lead.email):
                    result["validation"]["basic_format_valid"] = True
                    result["validation"]["normalized_email"] = lead.email.lower().strip()
                    parts = lead.email.split('@')
                    if len(parts) == 2:
                        result["validation"]["local_part"] = parts[0]
                        result["validation"]["domain"] = parts[1]
                        result["domain_info"] = await self._get_domain_info(parts[1])
            
        except Exception as e:
            result["errors"].append(f"Email enrichment error: {e}")
            logger.error(f"Email enrichment failed for lead {lead.id}: {e}")
        
        return result
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Basic email format validation using regex as fallback."""
        if not email:
            return False
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def _enrich_phone(self, lead: Lead) -> Dict[str, Any]:
        """Validate and format phone numbers."""
        result = {
            "original_phone": lead.phone,
            "validation": {},
            "formatted": {},
            "errors": []
        }
        
        try:
            if not lead.phone:
                result["errors"].append("No phone number provided")
                return result
            
            # Basic phone validation without phonenumbers library for now
            # Remove all non-digits
            phone_digits = re.sub(r'\D', '', lead.phone)
            
            if len(phone_digits) >= 10:
                result["validation"] = {
                    "is_valid": True,
                    "digits_only": phone_digits
                }
                
                # Basic formatting
                if len(phone_digits) == 10:
                    # US format
                    formatted = f"({phone_digits[:3]}) {phone_digits[3:6]}-{phone_digits[6:]}"
                    result["formatted"] = {
                        "national": formatted,
                        "e164": f"+1{phone_digits}"
                    }
                elif len(phone_digits) == 11 and phone_digits.startswith('1'):
                    # US with country code
                    formatted = f"({phone_digits[1:4]}) {phone_digits[4:7]}-{phone_digits[7:]}"
                    result["formatted"] = {
                        "national": formatted,
                        "e164": f"+{phone_digits}"
                    }
                else:
                    result["formatted"] = {
                        "international": f"+{phone_digits}"
                    }
            else:
                result["validation"] = {
                    "is_valid": False,
                    "error": "Phone number too short"
                }
                result["errors"].append("Phone number validation failed: too short")
            
        except Exception as e:
            result["errors"].append(f"Phone enrichment error: {e}")
            logger.error(f"Phone enrichment failed for lead {lead.id}: {e}")
        
        return result
    
    async def _enrich_company(self, lead: Lead) -> Dict[str, Any]:
        """Enrich company information using multiple data sources."""
        result = {
            "original_company": lead.company,
            "original_website": lead.website,
            "normalized_company": None,
            "industry": None,
            "size_estimate": None,
            "domain_info": {},
            "social_profiles": {},
            "sources": [],
            "errors": []
        }
        
        try:
            # Normalize company name
            if lead.company:
                result["normalized_company"] = self._normalize_company_name(lead.company)
                result["industry"] = self._classify_industry(lead.company, lead.job_title)
            
            # Enrich using website domain
            if lead.website:
                domain = self._extract_domain(lead.website)
                if domain:
                    result["domain_info"] = await self._get_domain_info(domain)
                    result["sources"].append("website")
            
            # Enrich using email domain if no website
            elif lead.email and '@' in lead.email:
                domain = lead.email.split('@')[1]
                result["domain_info"] = await self._get_domain_info(domain)
                result["sources"].append("email_domain")
            
            # Estimate company size based on available data
            result["size_estimate"] = self._estimate_company_size(lead, result)
            
        except Exception as e:
            result["errors"].append(f"Company enrichment error: {e}")
            logger.error(f"Company enrichment failed for lead {lead.id}: {e}")
        
        return result
    
    async def _enrich_social_profiles(self, lead: Lead) -> Dict[str, Any]:
        """Discover and validate social media profiles."""
        result = {
            "linkedin": {"url": lead.linkedin_url, "validated": False},
            "discovered_profiles": [],
            "sources": [],
            "errors": []
        }
        
        try:
            # Validate existing LinkedIn URL
            if lead.linkedin_url:
                result["linkedin"]["validated"] = self._validate_linkedin_url(lead.linkedin_url)
                if result["linkedin"]["validated"]:
                    result["sources"].append("existing_linkedin")
            
            # Discover additional profiles based on email/name
            if lead.email:
                discovered = await self._discover_social_profiles(lead.first_name, lead.last_name, lead.email)
                result["discovered_profiles"] = discovered
                if discovered:
                    result["sources"].append("social_discovery")
            
        except Exception as e:
            result["errors"].append(f"Social profile enrichment error: {e}")
            logger.error(f"Social profile enrichment failed for lead {lead.id}: {e}")
        
        return result
    
    async def _normalize_lead_data(self, lead: Lead) -> Dict[str, Any]:
        """Normalize and clean lead data."""
        result = {
            "original_data": {},
            "normalized_data": {},
            "changes": [],
            "errors": []
        }
        
        try:
            # Store original data
            result["original_data"] = {
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "job_title": lead.job_title
            }
            
            # Normalize names
            normalized_first = self._normalize_name(lead.first_name)
            normalized_last = self._normalize_name(lead.last_name)
            
            # Normalize company name
            normalized_company = None
            if lead.company:
                normalized_company = self._normalize_company_name(lead.company)
            
            # Normalize job title
            normalized_job_title = None
            if lead.job_title:
                normalized_job_title = self._normalize_job_title(lead.job_title)
            
            result["normalized_data"] = {
                "first_name": normalized_first,
                "last_name": normalized_last,
                "company": normalized_company,
                "job_title": normalized_job_title
            }
            
            # Track changes
            for field in result["original_data"]:
                if result["original_data"][field] != result["normalized_data"][field]:
                    result["changes"].append({
                        "field": field,
                        "from": result["original_data"][field],
                        "to": result["normalized_data"][field]
                    })
            
        except Exception as e:
            result["errors"].append(f"Data normalization error: {e}")
            logger.error(f"Data normalization failed for lead {lead.id}: {e}")
        
        return result
    
    async def _check_duplicates(self, lead: Lead) -> Dict[str, Any]:
        """Check for potential duplicate leads."""
        result = {
            "potential_duplicates": [],
            "duplicate_score": 0,
            "matching_criteria": [],
            "errors": []
        }
        
        try:
            # Query for potential duplicates
            duplicates = []
            
            # Exact email match
            if lead.email:
                email_matches = self.db.query(Lead).filter(
                    and_(Lead.email == lead.email, Lead.id != lead.id, Lead.organization_id == lead.organization_id)
                ).all()
                
                for match in email_matches:
                    duplicates.append({
                        "lead_id": match.id,
                        "match_type": "exact_email",
                        "score": 100,
                        "matched_field": "email",
                        "matched_value": match.email
                    })
            
            # Name + company match
            if lead.first_name and lead.last_name and lead.company:
                name_company_matches = self.db.query(Lead).filter(
                    and_(
                        Lead.first_name.ilike(f"%{lead.first_name}%"),
                        Lead.last_name.ilike(f"%{lead.last_name}%"),
                        Lead.company.ilike(f"%{lead.company}%"),
                        Lead.id != lead.id,
                        Lead.organization_id == lead.organization_id
                    )
                ).all()
                
                for match in name_company_matches:
                    duplicates.append({
                        "lead_id": match.id,
                        "match_type": "name_company",
                        "score": 85,
                        "matched_field": "name_company",
                        "matched_value": f"{match.first_name} {match.last_name} @ {match.company}"
                    })
            
            # Phone number match
            if lead.phone:
                phone_matches = self.db.query(Lead).filter(
                    and_(Lead.phone == lead.phone, Lead.id != lead.id, Lead.organization_id == lead.organization_id)
                ).all()
                
                for match in phone_matches:
                    duplicates.append({
                        "lead_id": match.id,
                        "match_type": "exact_phone",
                        "score": 90,
                        "matched_field": "phone",
                        "matched_value": match.phone
                    })
            
            result["potential_duplicates"] = duplicates
            if duplicates:
                result["duplicate_score"] = max([d["score"] for d in duplicates])
                result["matching_criteria"] = list(set([d["match_type"] for d in duplicates]))
            
        except Exception as e:
            result["errors"].append(f"Duplicate check error: {e}")
            logger.error(f"Duplicate check failed for lead {lead.id}: {e}")
        
        return result

    # Utility methods for data processing
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a person's name."""
        if not name:
            return name
        
        # Remove extra spaces, capitalize properly
        normalized = ' '.join(word.capitalize() for word in name.strip().split())
        
        # Handle common name patterns
        normalized = normalized.replace("'S", "'s")  # McDonald's -> McDonald's
        normalized = re.sub(r'\b(Mc|Mac)([a-z])', lambda m: m.group(1) + m.group(2).upper(), normalized)
        
        return normalized
    
    def _normalize_company_name(self, company: str) -> str:
        """Normalize company name."""
        if not company:
            return company
        
        normalized = company.strip()
        
        # Remove common suffixes for comparison
        lower_normalized = normalized.lower()
        for suffix in self.company_suffixes:
            if lower_normalized.endswith(f' {suffix}'):
                # Keep the suffix but normalize it
                normalized = normalized[:-len(suffix)].strip() + ' ' + suffix.upper()
                break
        
        return normalized
    
    def _normalize_job_title(self, title: str) -> str:
        """Normalize job title."""
        if not title:
            return title
        
        # Capitalize each word but handle common abbreviations
        normalized = title.strip().title()
        
        # Common abbreviations that should be uppercase
        abbreviations = ['CEO', 'CTO', 'CFO', 'CMO', 'COO', 'VP', 'SVP', 'EVP', 'HR', 'IT', 'QA', 'UI', 'UX']
        
        for abbr in abbreviations:
            normalized = re.sub(r'\b' + re.escape(abbr.lower()) + r'\b', abbr, normalized, flags=re.IGNORECASE)
        
        return normalized
    
    def _classify_industry(self, company: str, job_title: str) -> Optional[str]:
        """Classify industry based on company name and job title."""
        if not company and not job_title:
            return None
        
        text_to_analyze = f"{company or ''} {job_title or ''}".lower()
        
        for industry, keywords in self.industry_keywords.items():
            for keyword in keywords:
                if keyword in text_to_analyze:
                    return industry
        
        return None
    
    def _estimate_company_size(self, lead: Lead, company_data: Dict) -> Optional[str]:
        """Estimate company size based on available data."""
        # This is a simplified estimation - in production you'd use external APIs
        
        # Check domain info for clues
        domain_info = company_data.get("domain_info", {})
        
        # Simple heuristics based on job title
        if lead.job_title:
            title_lower = lead.job_title.lower()
            if any(word in title_lower for word in ['ceo', 'founder', 'owner']):
                return 'startup'  # 1-10 employees
            elif any(word in title_lower for word in ['vp', 'vice president', 'director']):
                return 'medium'   # 51-200 employees
            elif any(word in title_lower for word in ['senior', 'lead', 'principal']):
                return 'small'    # 11-50 employees
        
        return 'unknown'
    
    async def _get_domain_info(self, domain: str) -> Dict[str, Any]:
        """Get domain information using basic lookup (placeholder for WHOIS)."""
        info = {
            "domain": domain,
            "basic_info": {},
            "errors": []
        }
        
        try:
            # For now, just store basic domain info
            # In production, you'd integrate with WHOIS services
            info["basic_info"] = {
                "domain_name": domain,
                "extracted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            info["errors"].append(f"Domain lookup failed: {e}")
        
        return info
    
    def _extract_domain(self, website: str) -> Optional[str]:
        """Extract domain from website URL."""
        if not website:
            return None
        
        # Remove protocol and www
        domain = website.lower()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0]  # Remove path
        
        return domain if '.' in domain else None
    
    def _validate_linkedin_url(self, url: str) -> bool:
        """Validate LinkedIn URL format."""
        if not url:
            return False
        
        linkedin_pattern = r'https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'
        return bool(re.match(linkedin_pattern, url))
    
    async def _discover_social_profiles(self, first_name: str, last_name: str, email: str) -> List[Dict]:
        """Discover social media profiles (placeholder for external API integration)."""
        # In production, this would integrate with services like:
        # - Clearbit Enrichment API
        # - FullContact Person API
        # - Hunter.io
        # - Apollo.io
        
        discovered = []
        
        # For now, return empty list with note about external integration
        # This is where you'd implement actual social discovery logic
        
        return discovered
    
    def _get_lead_snapshot(self, lead: Lead) -> Dict[str, Any]:
        """Get a snapshot of current lead data."""
        return {
            "id": lead.id,
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "company": lead.company,
            "job_title": lead.job_title,
            "phone": lead.phone,
            "website": lead.website,
            "linkedin_url": lead.linkedin_url,
            "custom_fields": lead.custom_fields,
            "tags": lead.tags
        }
    
    async def _apply_enrichment_to_lead(self, lead: Lead, enrichment_results: Dict[str, Any]) -> None:
        """Apply enriched data back to the lead."""
        try:
            updated_fields = []
            
            # Apply email normalization
            email_data = enrichment_results["enriched_data"].get("email", {})
            if email_data.get("validation", {}).get("is_valid") and email_data["validation"].get("normalized_email"):
                if lead.email != email_data["validation"]["normalized_email"]:
                    lead.email = email_data["validation"]["normalized_email"]
                    updated_fields.append("email")
            
            # Apply phone formatting
            phone_data = enrichment_results["enriched_data"].get("phone", {})
            if phone_data.get("validation", {}).get("is_valid") and phone_data["formatted"].get("e164"):
                if lead.phone != phone_data["formatted"]["e164"]:
                    lead.phone = phone_data["formatted"]["e164"]
                    updated_fields.append("phone")
            
            # Apply data normalization
            norm_data = enrichment_results["enriched_data"].get("normalization", {})
            if norm_data.get("normalized_data"):
                for field, value in norm_data["normalized_data"].items():
                    if value and getattr(lead, field) != value:
                        setattr(lead, field, value)
                        updated_fields.append(field)
            
            # Update custom fields with enrichment data
            custom_fields = lead.custom_fields or {}
            
            # Add enrichment metadata
            custom_fields["enrichment"] = {
                "last_enriched": datetime.utcnow().isoformat(),
                "enrichment_types": enrichment_results["enrichment_types"],
                "data_sources": enrichment_results["data_sources"]
            }
            
            # Add company information
            company_data = enrichment_results["enriched_data"].get("company", {})
            if company_data.get("industry"):
                custom_fields["industry"] = company_data["industry"]
            if company_data.get("size_estimate"):
                custom_fields["company_size"] = company_data["size_estimate"]
            
            # Add validation results
            if enrichment_results["validation_results"]:
                custom_fields["validation"] = enrichment_results["validation_results"]
            
            # Add duplicate information
            dedup_data = enrichment_results["enriched_data"].get("deduplication", {})
            if dedup_data.get("potential_duplicates"):
                custom_fields["duplicate_check"] = {
                    "checked_at": datetime.utcnow().isoformat(),
                    "duplicate_score": dedup_data["duplicate_score"],
                    "potential_duplicates_count": len(dedup_data["potential_duplicates"])
                }
            
            lead.custom_fields = custom_fields
            updated_fields.append("custom_fields")
            
            # Update the lead's updated timestamp
            lead.updated_at = datetime.utcnow()
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Applied enrichment to lead {lead.id}, updated fields: {updated_fields}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to apply enrichment to lead {lead.id}: {e}")
            raise
    
    async def _log_enrichment_activity(self, lead_id: int, enrichment_results: Dict[str, Any]) -> None:
        """Log enrichment activity to activity log."""
        try:
            activity_log = ActivityLog(
                lead_id=lead_id,
                activity_type="lead_enriched",
                description=f"Lead data enriched with {', '.join(enrichment_results['enrichment_types'])}",
                activity_metadata={
                    "enrichment_types": enrichment_results["enrichment_types"],
                    "data_sources": enrichment_results["data_sources"],
                    "processing_time_ms": enrichment_results["metadata"]["processing_time_ms"],
                    "errors": enrichment_results["errors"],
                    "validation_results": enrichment_results["validation_results"]
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(activity_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log enrichment activity for lead {lead_id}: {e}")
    
    async def bulk_enrich_leads(
        self, 
        organization_id: int, 
        lead_ids: Optional[List[int]] = None,
        enrichment_types: Optional[List[str]] = None,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Bulk enrichment of multiple leads with rate limiting and error handling.
        """
        try:
            # Get leads to enrich
            query = self.db.query(Lead).filter(Lead.organization_id == organization_id)
            if lead_ids:
                query = query.filter(Lead.id.in_(lead_ids))
            
            leads = query.all()
            
            if not leads:
                return {
                    "total_leads": 0,
                    "enriched_leads": 0,
                    "failed_leads": 0,
                    "results": []
                }
            
            results = {
                "total_leads": len(leads),
                "enriched_leads": 0,
                "failed_leads": 0,
                "results": [],
                "errors": []
            }
            
            # Process in batches to avoid overwhelming external APIs
            for i in range(0, len(leads), batch_size):
                batch = leads[i:i + batch_size]
                
                # Process batch concurrently
                tasks = []
                for lead in batch:
                    task = self.enrich_lead(lead.id, enrichment_types)
                    tasks.append(task)
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        results["failed_leads"] += 1
                        results["errors"].append({
                            "lead_id": batch[j].id,
                            "error": str(result)
                        })
                    else:
                        results["enriched_leads"] += 1
                        results["results"].append(result)
                
                # Rate limiting between batches
                if i + batch_size < len(leads):
                    await asyncio.sleep(1)  # 1 second delay between batches
            
            logger.info(f"Bulk enrichment completed: {results['enriched_leads']}/{results['total_leads']} leads enriched")
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk enrichment failed for organization {organization_id}: {e}")
            raise 