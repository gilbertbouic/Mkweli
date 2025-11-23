from app import app
from models import Individual, Entity

def direct_search():
    with app.app_context():
        search_name = "Eric Badege"
        
        print(f"Direct search for: {search_name}")
        
        # Direct name match
        direct_matches = Individual.query.filter(Individual.name.ilike(f'%{search_name}%')).all()
        print(f"Direct matches: {len(direct_matches)}")
        for match in direct_matches:
            print(f"  - {match.name} ({match.source})")
        
        # Partial matches
        print(f"\nPartial matches:")
        for name_part in search_name.lower().split():
            matches = Individual.query.filter(Individual.name.ilike(f'%{name_part}%')).all()
            print(f"  '{name_part}': {len(matches)} matches")
            for match in matches[:3]:  # Show first 3
                print(f"    - {match.name}")

if __name__ == '__main__':
    direct_search()
