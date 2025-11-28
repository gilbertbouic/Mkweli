"""
Tests for XML format auto-detection in SanctionsService.

This module tests the _detect_format method which identifies
the sanctions list format based on XML structure rather than filename.
"""
import unittest
import unittest.mock
import xml.etree.ElementTree as ET
import sys
import os

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.sanctions_service import SanctionsService


class TestFormatDetection(unittest.TestCase):
    """Tests for the _detect_format method in SanctionsService"""
    
    def setUp(self):
        """Create a SanctionsService instance for testing without loading data"""
        # Patch the initialization to skip loading actual files
        with unittest.mock.patch.object(SanctionsService, '_load_or_parse_sanctions'):
            self.service = SanctionsService(data_dir='/nonexistent')
    
    def test_detect_eu_format_by_namespace(self):
        """Test EU format detection via namespace"""
        xml = '''<?xml version="1.0"?>
        <export xmlns="http://eu.europa.ec/fpi/fsd/export">
            <sanctionEntity>
                <nameAlias wholeName="Test Entity"/>
            </sanctionEntity>
        </export>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'EU')
    
    def test_detect_eu_format_by_sanction_entity(self):
        """Test EU format detection via sanctionEntity elements"""
        xml = '''<?xml version="1.0"?>
        <export>
            <sanctionEntity>
                <nameAlias wholeName="Test Entity"/>
            </sanctionEntity>
        </export>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'EU')
    
    def test_detect_ofac_format_by_namespace(self):
        """Test OFAC format detection via namespace"""
        xml = '''<?xml version="1.0"?>
        <sanctionsData xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML">
            <entities>
                <entity>
                    <names><name><translations><translation><formattedFullName>Test</formattedFullName></translation></translations></name></names>
                </entity>
            </entities>
        </sanctionsData>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'OFAC')
    
    def test_detect_ofac_format_by_root_tag(self):
        """Test OFAC format detection via sanctionsData root tag"""
        xml = '''<?xml version="1.0"?>
        <sanctionsData>
            <entities>
                <entity><names><name>Test</name></names></entity>
            </entities>
        </sanctionsData>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'OFAC')
    
    def test_detect_ofac_format_by_entities_structure(self):
        """Test OFAC format detection via entities/entity structure"""
        xml = '''<?xml version="1.0"?>
        <root>
            <entities>
                <entity><names><name>Test</name></names></entity>
            </entities>
        </root>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'OFAC')
    
    def test_detect_un_format_with_name6_and_individual_entity_ship(self):
        """Test UN format detection with Name6 and IndividualEntityShip"""
        xml = '''<?xml version="1.0"?>
        <Designations>
            <Designation>
                <Names>
                    <Name>
                        <Name6>Test Individual</Name6>
                    </Name>
                </Names>
                <IndividualEntityShip>Individual</IndividualEntityShip>
            </Designation>
        </Designations>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'UN')
    
    def test_detect_uk_format_with_plain_name(self):
        """Test UK format detection with plain Name elements"""
        xml = '''<?xml version="1.0"?>
        <Designations>
            <Designation>
                <Name>Test Individual</Name>
            </Designation>
        </Designations>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'UK')
    
    def test_detect_uk_format_default_for_designations(self):
        """Test UK format as default for Designations root"""
        xml = '''<?xml version="1.0"?>
        <Designations>
            <Designation>
                <SomeOtherElement>Data</SomeOtherElement>
            </Designation>
        </Designations>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'UK')
    
    def test_detect_generic_format_for_unknown_structure(self):
        """Test generic format detection for unknown structure"""
        xml = '''<?xml version="1.0"?>
        <unknown>
            <item>
                <name>Test</name>
            </item>
        </unknown>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'generic')
    
    def test_eu_takes_precedence_over_other_checks(self):
        """Test EU namespace takes precedence over other markers"""
        xml = '''<?xml version="1.0"?>
        <Designations xmlns="http://eu.europa.ec/fpi/fsd/export">
            <Designation>
                <Name6>Test</Name6>
                <IndividualEntityShip>Individual</IndividualEntityShip>
            </Designation>
        </Designations>'''
        root = ET.fromstring(xml)
        # EU namespace should be detected even with UN markers
        self.assertEqual(self.service._detect_format(root), 'EU')
    
    def test_ofac_takes_precedence_over_designations(self):
        """Test OFAC namespace takes precedence"""
        xml = '''<?xml version="1.0"?>
        <sanctionsData xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML">
        </sanctionsData>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'OFAC')
    
    def test_handles_namespaced_elements(self):
        """Test detection with namespaced child elements"""
        xml = '''<?xml version="1.0"?>
        <ns:export xmlns:ns="http://eu.europa.ec/fpi/fsd/export">
            <ns:sanctionEntity>
                <ns:nameAlias wholeName="Test"/>
            </ns:sanctionEntity>
        </ns:export>'''
        root = ET.fromstring(xml)
        self.assertEqual(self.service._detect_format(root), 'EU')


class TestFormatDetectionIntegration(unittest.TestCase):
    """Integration tests for format detection with actual file parsing"""
    
    def test_parser_version_incremented(self):
        """Test that parser version was incremented for cache invalidation"""
        from app.sanctions_service import PARSER_VERSION
        self.assertGreaterEqual(PARSER_VERSION, 3, 
            "Parser version should be at least 3 after format detection changes")


if __name__ == '__main__':
    unittest.main()
