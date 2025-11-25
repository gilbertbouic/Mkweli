# check_parser_methods.py
import importlib.util

# Load the XML parser module
spec = importlib.util.spec_from_file_location("xml_parser", "app/xml_sanctions_parser.py")
xml_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xml_module)

# Check available methods
parser = xml_module.UniversalSanctionsParser()
print("📋 Available methods in UniversalSanctionsParser:")
for method_name in dir(parser):
    if not method_name.startswith('_'):
        print(f"  - {method_name}")

# Also check if there are any attributes with data
print(f"\n📊 Parser attributes:")
print(f"  entities: {hasattr(parser, 'entities')}")
if hasattr(parser, 'entities'):
    print(f"  Number of entities: {len(parser.entities)}")
