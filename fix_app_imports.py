#!/usr/bin/env python3
"""
Fix imports in app.py
"""
import re

# Read app.py
with open('app.py', 'r') as f:
    content = f.read()

# Replace the check_sanctions route
old_route = '''@app.route('/check_sanctions', methods=['POST'])
def check_sanctions():
    try:
        client_name = request.form.get('client_name', '').strip()
        client_type = request.form.get('client_type', 'Individual')
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Use the XML parser directly for better matching
        from app.xml_sanctions_parser import UniversalSanctionsParser
        parser = UniversalSanctionsParser()
        entities = parser.get_all_entities()
        
        from app.advanced_fuzzy_matcher import OptimalFuzzyMatcher
        matcher = OptimalFuzzyMatcher(entities)
        
        # Use a lower threshold to catch more matches
        matches = matcher.find_matches(client_name, threshold=70)
        
        # Log the screening
        screening_result = {
            'client_name': client_name,
            'client_type': client_type,
            'matches_found': len(matches),
            'matches': matches,
            'screening_time': datetime.utcnow().isoformat(),
        }
        
        # Return results
        return jsonify({
            'client_name': client_name,
            'client_type': client_type,
            'matches_found': len(matches),
            'matches': matches[:5],  # Return top 5 matches
            'screening_time': screening_result['screening_time']
        })
        
    except Exception as e:
        print(f"Error in sanctions check: {e}")
        return jsonify({'error': 'Screening failed'}), 500'''

new_route = '''@app.route('/check_sanctions', methods=['POST'])
def check_sanctions():
    try:
        client_name = request.form.get('client_name', '').strip()
        client_type = request.form.get('client_type', 'Individual')
        
        if not client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Use direct imports from the app directory
        import sys
        sys.path.append('app')
        from robust_sanctions_parser import RobustSanctionsParser
        from advanced_fuzzy_matcher import OptimalFuzzyMatcher
        
        # Parse sanctions data
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        
        # Find matches
        matcher = OptimalFuzzyMatcher(entities)
        matches = matcher.find_matches(client_name, threshold=70)
        
        # Return results
        return jsonify({
            'client_name': client_name,
            'client_type': client_type,
            'matches_found': len(matches),
            'matches': matches[:5],  # Return top 5 matches
            'screening_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error in sanctions check: {e}")
        return jsonify({'error': 'Screening failed'}), 500'''

# Replace the content
content = content.replace(old_route, new_route)

# Also fix the sanctions-stats route
old_stats = '''@app.route('/sanctions-stats')
def sanctions_stats():
    """Get sanctions list statistics"""
    try:
        from app.sanctions_service import get_sanctions_stats
        stats = get_sanctions_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'status': 'initializing',
            'message': 'Sanctions service is starting up...'
        })'''

new_stats = '''@app.route('/sanctions-stats')
def sanctions_stats():
    """Get sanctions list statistics"""
    try:
        import sys
        sys.path.append('app')
        from robust_sanctions_parser import RobustSanctionsParser
        parser = RobustSanctionsParser()
        entities = parser.parse_all_sanctions()
        return jsonify({
            'status': 'active',
            'entities_loaded': len(entities),
            'message': f'Loaded {len(entities)} sanction entities'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error loading sanctions: {str(e)}'
        })'''

content = content.replace(old_stats, new_stats)

# Write back
with open('app.py', 'w') as f:
    f.write(content)

print("✅ Fixed imports in app.py")
