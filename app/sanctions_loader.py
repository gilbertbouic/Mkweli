import pandas as pd
import os
import logging
from typing import List, Dict
import xml.etree.ElementTree as ET

class SanctionsLoader:
    def __init__(self):
        self.sanctions_data = []
        self.logger = logging.getLogger(__name__)

    def load_sanctions_data(self) -> List[Dict]:
        """Load sanctions data from various sources"""
        data_dir = "data"
        self.sanctions_data = []
        
        if not os.path.exists(data_dir):
            self.logger.error(f"Data directory '{data_dir}' not found")
            return self.sanctions_data

        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            
            try:
                if filename.endswith('.csv'):
                    self._load_csv(file_path)
                elif filename.endswith('.xml'):
                    self._load_xml(file_path)
                else:
                    self.logger.info(f"Skipping unsupported file type: {filename}")
            except Exception as e:
                self.logger.error(f"Error loading {filename}: {str(e)}")

        self.logger.info(f"Loaded {len(self.sanctions_data)} sanction entities")
        return self.sanctions_data

    def _load_csv(self, file_path: str):
        """Load data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            # Handle different CSV formats
            if 'name' in df.columns:
                for _, row in df.iterrows():
                    self.sanctions_data.append({
                        'name': str(row['name']),
                        'type': row.get('type', 'Entity'),
                        'source': os.path.basename(file_path),
                        'country': row.get('country', ''),
                        'reason': row.get('reason', '')
                    })
            elif 'Entity' in df.columns:
                for _, row in df.iterrows():
                    self.sanctions_data.append({
                        'name': str(row['Entity']),
                        'type': 'Entity',
                        'source': os.path.basename(file_path),
                        'country': row.get('Country', ''),
                        'reason': row.get('Reason', '')
                    })
        except Exception as e:
            self.logger.error(f"Error reading CSV {file_path}: {str(e)}")

    def _load_xml(self, file_path: str):
        """Basic XML loader for sanctions data"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Try common XML structures for sanctions data
            for elem in root.iter():
                name = None
                if elem.tag in ['ENTITY', 'ENTITY_NAME', 'NAME', 'INDIVIDUAL']:
                    name = elem.text
                elif elem.attrib.get('name'):
                    name = elem.attrib.get('name')
                
                if name and len(name.strip()) > 2:  # Basic validation
                    self.sanctions_data.append({
                        'name': name.strip(),
                        'type': 'Entity',
                        'source': os.path.basename(file_path),
                        'country': '',
                        'reason': ''
                    })
                    
        except Exception as e:
            self.logger.warning(f"Could not parse XML {file_path}: {str(e)}")
