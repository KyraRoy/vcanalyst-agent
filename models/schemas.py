from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
from datetime import datetime

class Citation(BaseModel):
    url: HttpUrl
    snippet: str
    source_type: str  # "website", "news", "linkedin", "google"
    timestamp: datetime

class Section(BaseModel):
    text: Optional[str] = None
    bullets: List[str] = []
    metrics: Dict[str, str] = {}
    citations: List[Citation] = []
    
    def has_content(self) -> bool:
        """Check if section has any meaningful content"""
        return bool(self.text or self.bullets or self.metrics)

class StructuredCompanyDoc(BaseModel):
    """Structured company document with all analysis sections"""
    name: str
    intro: Section = Field(default_factory=Section)
    problem: Section = Field(default_factory=Section)
    solution: Section = Field(default_factory=Section)
    product: Section = Field(default_factory=Section)
    business_model: Section = Field(default_factory=Section)
    market: Section = Field(default_factory=Section)
    traction: Section = Field(default_factory=Section)
    growth_strategy: Section = Field(default_factory=Section)
    team: Section = Field(default_factory=Section)
    competitors: Section = Field(default_factory=Section)
    financials: Section = Field(default_factory=Section)
    risks: Section = Field(default_factory=Section)
    timing: Section = Field(default_factory=Section)
    moat: Section = Field(default_factory=Section)
    recommendations: Section = Field(default_factory=Section)
    
    def get_populated_sections(self) -> Dict[str, Section]:
        """Return only sections that have content"""
        populated = {}
        for field_name, section in self.dict().items():
            if isinstance(section, dict) and field_name not in ['name', 'website', 'contact', 'missing_fields']:
                section_obj = Section(**section)
                if section_obj.has_content():
                    populated[field_name] = section_obj
        return populated
    
    def get_missing_fields(self) -> List[str]:
        """Return field names that have no content"""
        missing = []
        for field_name, section in self.dict().items():
            if isinstance(section, dict) and field_name not in ['name', 'website', 'contact', 'missing_fields']:
                section_obj = Section(**section)
                if not section_obj.has_content():
                    missing.append(field_name)
        return missing

class RawDoc(BaseModel):
    """Raw document from web scraping"""
    url: HttpUrl
    title: str
    text: str
    source_type: str
    timestamp: datetime 