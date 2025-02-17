import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
import sys
import re

def load_bibtex(filename):
    with open(filename) as bibtex_file:
        return bibtexparser.load(bibtex_file)

def normalize_title(title):
    """More robust title normalization"""
    if not title:
        return ''
    
    # Convert to lowercase
    title = title.lower()
    
    # Replace hyphens with spaces
    title = title.replace('-', ' ')
    
    # Remove braces
    title = title.replace('{', '').replace('}', '')
    
    # Remove all other punctuation and special characters
    title = re.sub(r'[^\w\s]', '', title)
    
    # Remove extra whitespace
    title = ' '.join(title.split())
    
    return title

def is_talk(entry):
    """Check if entry is a talk/presentation"""
    entry_type = entry.get('ENTRYTYPE', '').lower()
    if entry_type == 'unpublished':
        return True
    return False

def merge_entries(new_entry, orig_entry):
    """Merge entries, preserving formatting and fields from new_entry while adding missing fields from orig_entry"""
    # Fields to copy from original if they exist
    preserve_fields = ['author+an', 'note', 'keywords', 'presort', 'label']
    
    merged = new_entry.copy()
    
    # Add fields from original that don't exist in new entry
    for field in preserve_fields:
        if field in orig_entry and field not in merged:
            merged[field] = orig_entry[field]
            
    # Special handling for keywords
    if 'keywords' in orig_entry and 'keywords' in merged:
        orig_keywords = set(k.strip() for k in orig_entry['keywords'].split(','))
        new_keywords = set(k.strip() for k in merged['keywords'].split(','))
        merged['keywords'] = ', '.join(sorted(orig_keywords | new_keywords))
    
    return merged

def print_entry_debug(entry, source=""):
    """Print debug info for an entry"""
    entry_type = entry.get('ENTRYTYPE', 'Unknown type')
    print(f"\n{source} Entry:")
    print(f"Type: {entry_type}")
    print(f"ID: {entry.get('ID', 'No ID')}")
    print(f"Title: {entry.get('title', 'No title')}")
    print(f"Normalized title: {normalize_title(entry.get('title', ''))}")

def merge_bibtex(original_file, new_file, output_file):
    # Load both files
    original_db = load_bibtex(original_file)
    new_db = load_bibtex(new_file)
    
    # Create title-to-entry mappings, excluding talks
    original_entries = {normalize_title(entry.get('title', '')): entry 
                       for entry in original_db.entries 
                       if not is_talk(entry)}
    new_entries = {normalize_title(entry.get('title', '')): entry 
                   for entry in new_db.entries 
                   if not is_talk(entry)}
    
    # Print all normalized titles for debugging
    print("\nAll original titles (excluding talks):")
    for title in sorted(original_entries.keys()):
        print(f"  {title}")
    print("\nAll new titles (excluding talks):")
    for title in sorted(new_entries.keys()):
        print(f"  {title}")
    
    merged_db = BibDatabase()
    merged_entries = []
    stats = {
        'total_original': len(original_db.entries),
        'total_new': len(new_db.entries),
        'matched': 0,
        'unmatched_original': 0,
        'unmatched_new': 0
    }
    
    # Process all new entries
    for new_entry in new_db.entries:
        if is_talk(new_entry):
            continue
            
        norm_title = normalize_title(new_entry.get('title', ''))
        if norm_title in original_entries:
            merged_entry = merge_entries(new_entry, original_entries[norm_title])
            merged_entries.append(merged_entry)
            stats['matched'] += 1
        else:
            merged_entries.append(new_entry)
            stats['unmatched_new'] += 1
            print_entry_debug(new_entry, "Unmatched New")
    
    # Add any original entries that weren't in new (excluding talks)
    for orig_entry in original_db.entries:
        if is_talk(orig_entry):
            continue
            
        norm_title = normalize_title(orig_entry.get('title', ''))
        if norm_title not in new_entries:
            merged_entries.append(orig_entry)
            stats['unmatched_original'] += 1
            print_entry_debug(orig_entry, "Unmatched Original")
    
    # Sort entries by ID
    merged_entries.sort(key=lambda x: x.get('ID', ''))
    merged_db.entries = merged_entries
    
    # Write merged database
    with open(output_file, 'w') as bibtex_file:
        bibtexparser.dump(merged_db, bibtex_file)
    
    # Print statistics
    print("\nMerge Statistics:")
    print(f"Original entries (excluding talks): {len(original_entries)}")
    print(f"New entries (excluding talks): {len(new_entries)}")
    print(f"Matched and merged: {stats['matched']}")
    print(f"Unmatched from original: {stats['unmatched_original']}")
    print(f"Unmatched from new: {stats['unmatched_new']}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python merge_bibtex.py original.bib new.bib output.bib")
        sys.exit(1)
    
    merge_bibtex(sys.argv[1], sys.argv[2], sys.argv[3])