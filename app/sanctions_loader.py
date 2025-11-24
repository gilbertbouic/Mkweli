import pandas as pd
import os
from pathlib import Path
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SanctionsLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.sanctions_data = []
        
    def load_all_sanctions(self) -> List[Dict[str, Any]]:
        """Load all sanctions files from data directory"""
        if not self.data_dir.exists():
            logger.error(f"Data directory {self.data_dir} does not exist")
            return []
            
        all_entities = []
        
        for file_path in self.data_dir.iterdir():
            if file_path.is_file():
                entities = self._load_file(file_path)
                all_entities.extend(entities)
                
        logger.info(f"Loaded {len(all_entities)} total entities from sanctions lists")
        return all_entities
    
    def _load_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load a single sanctions file"""
        try:
            file_type = file_path.suffix.lower()
            
            if file_type == '.csv':
                return self._load_csv(file_path)
            elif file_type in ['.xlsx', '.xls']:
                return self._load_excel(file_path)
            elif file_type == '.ods':
                return self._load_ods(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type} for {file_path.name}")
                return []
                
        except Exception as e:
            logger.error(f"Error loading {file_path.name}: {e}")
            return []
    
    def _load_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load CSV file with multiple encoding attempts"""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                return self._process_dataframe(df, file_path.name)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"CSV encoding {encoding} failed: {e}")
                continue
                
        logger.error(f"Could not read CSV {file_path.name} with any encoding")
        return []
    
    def _load_excel(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load Excel file"""
        try:
            # Try reading all sheets
            excel_file = pd.ExcelFile(file_path)
            all_entities = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    entities = self._process_dataframe(df, f"{file_path.name}[{sheet_name}]")
                    all_entities.extend(entities)
                except Exception as e:
                    logger.warning(f"Error reading sheet {sheet_name}: {e}")
                    
            return all_entities
            
        except Exception as e:
            logger.error(f"Error reading Excel file {file_path.name}: {e}")
            return []
    
    def _load_ods(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load ODS file"""
        try:
            df = pd.read_excel(file_path, engine='odf')
            return self._process_dataframe(df, file_path.name)
        except Exception as e:
            logger.error(f"Error reading ODS file {file_path.name}: {e}")
            return []
    
    def _process_dataframe(self, df: pd.DataFrame, source: str) -> List[Dict[str, Any]]:
        """Process DataFrame into standardized entity format"""
        entities = []
        
        # Clean column names
        df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
        
        # Common sanctions list column patterns
        name_columns = ['name', 'entity_name', 'individual_name', 'company_name', 'target_name']
        country_columns = ['country', 'nationality', 'country_of_origin', 'address_country']
        
        for _, row in df.iterrows():
            entity = {
                'source': source,
                'raw_data': row.to_dict()
            }
            
            # Extract name
            entity['name'] = self._extract_field(row, name_columns)
            
            # Extract country
            entity['country'] = self._extract_field(row, country_columns)
            
            # Extract other common fields
            entity['type'] = self._extract_field(row, ['type', 'entity_type', 'target_type'])
            entity['reference'] = self._extract_field(row, ['reference', 'id', 'listing_id'])
            
            entities.append(entity)
            
        logger.info(f"Processed {len(entities)} entities from {source}")
        return entities
    
    def _extract_field(self, row, possible_columns):
        """Extract field value from possible column names"""
        for col in possible_columns:
            if col in row and pd.notna(row[col]):
                return str(row[col]).strip()
        return None
