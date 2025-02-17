import bibtexparser
import yaml
import sys
import re

# Configuration
SETTINGS = {
    'keywords': ['journal'],  # Base keywords required for all publications
    'selected_keywords': ['journal', 'web_selected'],  # Keywords required for selected publications
    'patent_keywords': ['patent'],  # Keywords for patents
    'sort_order': 'desc',     # 'desc' for newest first, 'asc' for oldest first
}

def parse_author_annotations(annotation_str):
    """Parse author+an field into a dict of author positions and their annotations"""
    if not annotation_str:
        return {}
    
    annotations = {}
    # Split by semicolon for multiple annotations
    for item in annotation_str.split(';'):
        item = item.strip()
        if not item:
            continue
        # Parse each annotation (e.g., "1=first" or "2=highlight, first")
        try:
            pos, flags = item.split('=')
            pos = int(pos)
            flags = [f.strip() for f in flags.split(',')]
            annotations[pos] = flags
        except ValueError:
            continue
    return annotations

def format_author_name(author, position, annotations):
    """Format author name with annotations (*, underline) based on position"""
    # Remove any extra spaces and split the name
    parts = [p.strip() for p in author.split(',')]
    if len(parts) == 2:
        lastname = parts[0]
        firstnames = parts[1]
    else:
        names = author.split()
        lastname = names[-1]
        firstnames = ' '.join(names[:-1])
    
    # Get initials for first/middle names
    initials = ''.join(name[0] for name in firstnames.split())
    formatted_name = f"{lastname} {initials}"  # Space instead of comma
    
    # Apply annotations based on position
    author_flags = annotations.get(position, [])
    
    # Add highlight/underline for highlighted authors
    if 'highlight' in author_flags:
        formatted_name = f"{{highlight}}{formatted_name}{{/highlight}}"
    
    # Add asterisk for first authors
    if 'first' in author_flags:
        formatted_name = f"{formatted_name}*"
    
    return formatted_name

def format_authors(author_string, author_annotations):
    """Format all authors with their annotations"""
    # Split authors by ' and ' (with spaces) to avoid splitting within names
    authors = [a.strip() for a in re.split(r'\s+and\s+', author_string)]
    
    # Parse author annotations
    annotations = parse_author_annotations(author_annotations)
    
    # Format each author name with their annotations
    formatted_authors = []
    for i, author in enumerate(authors, 1):  # 1-based indexing to match BibTeX
        formatted_name = format_author_name(author, i, annotations)
        formatted_authors.append(formatted_name)
    
    return ', '.join(formatted_authors)

def should_include_entry(entry, required_keywords):
    """Check if entry should be included based on required keywords"""
    keywords_str = entry.get('keywords', '')
    
    if not keywords_str:
        return False
    
    # Split keywords and clean them
    keywords = [k.strip().lower() for k in keywords_str.split(',')]
    
    # Check each required keyword
    for req_key in required_keywords:
        if req_key not in keywords:
            return False
    
    return True

def clean_title(title):
    """Clean title while preserving specific capitalizations"""
    # Remove braces and trailing period
    title = title.replace('{', '').replace('}', '').rstrip('.')
    
    # List of terms that should remain capitalized
    preserve_caps = ['CAR-T', 'DNA', 'RNA', 'T cell', 'B cell']
    
    # Create a temporary placeholder for preserved terms
    placeholder_map = {}
    for i, term in enumerate(preserve_caps):
        placeholder = f"__PRESERVED_{i}__"
        # Case insensitive search and replace
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(title):
            title = pattern.sub(placeholder, title)
            placeholder_map[placeholder] = term
    
    # Restore preserved capitalizations
    for placeholder, term in placeholder_map.items():
        title = title.replace(placeholder, term)
    
    return title

def convert_bibtex_to_yaml(bibtex_file, yaml_file, type='publications'):
    """Convert BibTeX to YAML with type-specific handling"""
    print(f"\nConverting {bibtex_file} to {yaml_file}")
    print(f"Type: {type}")
    
    with open(bibtex_file) as bibtex_f:
        bib_database = bibtexparser.load(bibtex_f)
    
    # Set required keywords based on type
    if type == 'selected':
        required_keywords = SETTINGS['selected_keywords']
    elif type == 'patents':
        required_keywords = SETTINGS['patent_keywords']
    else:  # regular publications
        required_keywords = SETTINGS['keywords']
        
    # Filter and convert entries
    entries = []
    for entry in bib_database.entries:
        if should_include_entry(entry, required_keywords):
            
            if type == 'patents':
                cleaned_entry = {
                    'title': clean_title(entry.get('title', '')),
                    'author': format_authors(
                        entry.get('author', ''),
                        entry.get('author+an', '')
                    ),
                    'year': entry.get('year', ''),
                    'number': entry.get('number', ''),  # Patent number
                    'assignee': entry.get('assignee', ''),  # Patent assignee
                    'status': entry.get('note', ''),  # Patent status in note field
                    'url': entry.get('url', '')  # Link to patent
                }
            else:
                # Keep existing publication format exactly as is
                cleaned_entry = {
                    'title': clean_title(entry.get('title', '')),
                    'author': format_authors(
                        entry.get('author', ''),
                        entry.get('author+an', '')
                    ),
                    'year': entry.get('year', ''),
                    'journal': entry.get('journal', ''),
                    'volume': entry.get('volume', ''),
                    'number': entry.get('number', ''),
                    'pages': entry.get('pages', '').replace('--', '–'),
                    'doi': entry.get('doi', ''),  # Add cleaned DOI
                    'pdf': entry.get('pdf', '')
                }
            entries.append(cleaned_entry)
    
    print(f"Found {len(entries)} matching entries")
    
    # Sort entries
    sort_reverse = SETTINGS['sort_order'].lower() == 'desc'
    entries.sort(key=lambda x: (int(x['year']), x['title']), reverse=sort_reverse)
    
    # Write to YAML file
    with open(yaml_file, 'w') as yaml_f:
        yaml.dump(entries, yaml_f, default_flow_style=False)

def main():
    cv_bibtex = "cv/bib/citations_merged.bib"
    # Generate all three types
    convert_bibtex_to_yaml(cv_bibtex, "data/publications.yaml", type='publications')
    convert_bibtex_to_yaml(cv_bibtex, "data/selected_publications.yaml", type='selected')
    convert_bibtex_to_yaml(cv_bibtex, "data/patents.yaml", type='patents')

if __name__ == "__main__":
    main() 