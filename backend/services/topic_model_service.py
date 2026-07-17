"""
Database service for LDA Topic Model integration with Supabase.
Handles fetching text data and storing topic analysis results.
"""

from database.supabase_client import get_supabase_client
from typing import List, Dict, Any, Optional
from datetime import datetime


class TopicModelDatabase:
    """Service for database operations related to topic modeling."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_candidate_texts(
        self, 
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Fetch text data from candidates table for topic analysis.
        
        Args:
            fields: List of text fields to fetch (default: stellenbeschreibung, verbesserungsvorschlaege)
            limit: Maximum number of records to fetch
            
        Returns:
            List of combined text strings
        """
        if fields is None:
            fields = ['stellenbeschreibung', 'verbesserungsvorschlaege']
        
        # Build query
        query = self.supabase.table('candidates').select(','.join(fields))
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        
        # Combine text fields
        texts = []
        for record in response.data:
            combined_text = ' '.join([
                str(record.get(field, '')) 
                for field in fields 
                if record.get(field)
            ])
            if combined_text.strip():
                texts.append(combined_text)
        
        return texts
    
    def get_employee_texts(
        self, 
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Fetch text data from employee table for topic analysis.
        
        Args:
            fields: List of text fields to fetch
            limit: Maximum number of records to fetch
            
        Returns:
            List of combined text strings
        """
        if fields is None:
            fields = [
                'jobbeschreibung', 
                'gut_am_arbeitgeber_finde_ich',
                'schlecht_am_arbeitgeber_finde_ich',
                'verbesserungsvorschlaege'
            ]
        
        # Build query - filter rows where at least one text field is not null
        query = self.supabase.table('employee').select(','.join(fields))
        
        # Nur Zeilen mit mindestens einem befüllten Textfeld abrufen
        or_filter = ','.join([f"{f}.not.is.null" for f in fields])
        query = query.or_(or_filter)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        
        # Combine text fields
        texts = []
        for record in response.data:
            combined_text = ' '.join([
                str(record.get(field, '')) 
                for field in fields 
                if record.get(field)
            ])
            if combined_text.strip():
                texts.append(combined_text)
        
        return texts
    
    def get_employee_texts_with_metadata(
        self, 
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch text data from employee table with metadata (including status/employee type).
        
        Args:
            fields: List of text fields to fetch
            limit: Maximum number of records to fetch
            
        Returns:
            List of dictionaries with 'text', 'status', and other metadata
        """
        if fields is None:
            fields = [
                'jobbeschreibung', 
                'gut_am_arbeitgeber_finde_ich',
                'schlecht_am_arbeitgeber_finde_ich',
                'verbesserungsvorschlaege'
            ]
        
        # Build query - include status field for employee type
        select_fields = fields + ['status', 'id']
        query = self.supabase.table('employee').select(','.join(select_fields))
        
        # Nur Zeilen mit mindestens einem befüllten Textfeld abrufen
        or_filter = ','.join([f"{f}.not.is.null" for f in fields])
        query = query.or_(or_filter)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        
        # Combine text fields and include metadata
        result = []
        for record in response.data:
            combined_text = ' '.join([
                str(record.get(field, '')) 
                for field in fields 
                if record.get(field)
            ])
            if combined_text.strip():
                result.append({
                    'text': combined_text,
                    'status': record.get('status', ''),
                    'id': record.get('id'),
                    'source': 'employee'
                })
        
        return result
    
    def get_all_texts(
        self,
        source: str = "both",
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch all text data for topic analysis.
        
        Args:
            source: Data source - "candidates", "employee", or "both"
            limit: Maximum number of records to fetch per source
            include_metadata: If True, include metadata like employee status for weighting
            
        Returns:
            Dictionary with texts and metadata
        """
        result = {
            "texts": [],
            "sources": [],
            "metadata": {
                "candidates_count": 0,
                "employee_count": 0,
                "total_count": 0
            }
        }
        
        if include_metadata:
            result["detailed_metadata"] = []
        
        if source in ["candidates", "both"]:
            candidate_texts = self.get_candidate_texts(limit=limit)
            result["texts"].extend(candidate_texts)
            result["sources"].extend(["candidates"] * len(candidate_texts))
            result["metadata"]["candidates_count"] = len(candidate_texts)
            
            if include_metadata:
                for text in candidate_texts:
                    result["detailed_metadata"].append({
                        'text': text,
                        'source': 'candidates',
                        'status': None
                    })
        
        if source in ["employee", "both"]:
            if include_metadata:
                employee_data = self.get_employee_texts_with_metadata(limit=limit)
                result["texts"].extend([item['text'] for item in employee_data])
                result["sources"].extend(["employee"] * len(employee_data))
                result["metadata"]["employee_count"] = len(employee_data)
                result["detailed_metadata"].extend(employee_data)
            else:
                employee_texts = self.get_employee_texts(limit=limit)
                result["texts"].extend(employee_texts)
                result["sources"].extend(["employee"] * len(employee_texts))
                result["metadata"]["employee_count"] = len(employee_texts)
        
        result["metadata"]["total_count"] = len(result["texts"])
        
        return result
    
    def get_candidate_by_id(self, candidate_id: int, include_company: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific candidate record.
        
        Args:
            candidate_id: ID of the candidate
            include_company: Whether to include company information via join
            
        Returns:
            Candidate record or None
        """
        if include_company:
            # Join with companies table to get company name
            response = self.supabase.table('candidates').select('*, companies(name)').eq('id', candidate_id).execute()
        else:
            response = self.supabase.table('candidates').select('*').eq('id', candidate_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    def get_employee_by_id(self, employee_id: int, include_company: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific employee record.
        
        Args:
            employee_id: ID of the employee
            include_company: Whether to include company information via join
            
        Returns:
            Employee record or None
        """
        if include_company:
            # Join with companies table to get company name
            response = self.supabase.table('employee').select('*, companies(name)').eq('id', employee_id).execute()
        else:
            response = self.supabase.table('employee').select('*').eq('id', employee_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics for topic modeling.
        
        Returns:
            Dictionary with statistics
        """
        # Count candidates
        candidates_response = self.supabase.table('candidates').select('id', count='exact').execute()
        
        # Count employees
        employee_response = self.supabase.table('employee').select('id', count='exact').execute()
        
        # Count companies
        companies_response = self.supabase.table('companies').select('id', count='exact').execute()
        
        return {
            "candidates_total": candidates_response.count,
            "employee_total": employee_response.count,
            "companies_total": companies_response.count,
            "total_records": candidates_response.count + employee_response.count,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Get all companies from the database.
        
        Returns:
            List of company records
        """
        response = self.supabase.table('companies').select('*').order('name').execute()
        return response.data if response.data else []
    
    def get_company_by_id(self, company_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific company record.
        
        Args:
            company_id: ID of the company
            
        Returns:
            Company record or None
        """
        response = self.supabase.table('companies').select('*').eq('id', company_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    def get_candidates_by_company(self, company_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch candidates for a specific company.
        
        Args:
            company_id: ID of the company
            limit: Maximum number of records to fetch
            
        Returns:
            List of candidate records
        """
        query = self.supabase.table('candidates').select('*').eq('company_id', company_id)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
    
    def get_employees_by_company(self, company_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch employees for a specific company.
        
        Args:
            company_id: ID of the company
            limit: Maximum number of records to fetch
            
        Returns:
            List of employee records
        """
        query = self.supabase.table('employee').select('*').eq('company_id', company_id)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data if response.data else []
