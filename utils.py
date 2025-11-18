# utils.py snippet - Add to existing: Parse and insert to DB with error handling.
from models import db, Individual, Entity, Alias, Address, Sanction

def incorporate_to_db(parsed_data):  # Called after parsing in update_sanctions_lists
    try:
        with db.session.begin():
            for source, entries in parsed_data.items():
                for entry in entries:
                    # Example for Individual (adapt for Entity; sanitize)
                    if 'individual' in entry.lower():  # Simple check; use XML tags
                        ind = Individual(reference_number=entry['ref'], name=entry['name'].strip(),  # Sanitize
                                         dob=entry.get('dob'), nationality=entry.get('nationality'),
                                         listed_on=entry.get('listed_on'), source=source)
                        db.session.add(ind)
                        # Add aliases/addresses (1-to-many)
                        for alias in entry.get('aliases', []):
                            db.session.add(Alias(individual_id=ind.id, alias_name=alias.strip()))
                        # Similar for Address, Sanction
            db.session.commit()
    except Exception as e:
        db.session.rollback()  # Error handling
        raise ValueError(f"DB insert error: {str(e)}")
