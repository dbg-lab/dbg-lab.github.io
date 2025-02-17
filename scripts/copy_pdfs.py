import yaml
import os
import shutil
from pathlib import Path
import re
import glob

# Configuration
PAPERPILE_BASE = "/Users/dbg/Library/CloudStorage/GoogleDrive-dbgoodman@gmail.com/My Drive/Paperpile/All Papers"
STATIC_DIR = "static/pub_pdfs"

def get_pdf_path(title, authors, year):
    """Convert publication title and authors to expected PDF path"""
    # Clean up highlight tags, asterisks, and get first author's surname
    authors = re.sub(r'{highlight}|{/highlight}|\*', '', authors)
    
    first_author_full = authors.split(',')[0].strip()
    # Get surname by taking first word and removing any initials
    first_author = re.split(r'\s+[A-Z](\s+|[A-Z]|\.|$)', first_author_full)[0]
    first_letter = first_author[0].upper()
    
    # Clean and format the title
    title = ' '.join(title.split())  # Remove extra whitespace and newlines
    title = title.replace(':', ' -')  # Replace colons with hyphens (with spaces)
    
    # Construct start of filename (first 72 chars) for glob matching
    start_name = f"{first_author} et al. {year} - {title}"[:72]
    pattern = os.path.join(PAPERPILE_BASE, first_letter, start_name + "*.pdf")
    print(f"\nLooking for pattern: {pattern}")  # Debug print
    
    # Try to find matching file
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return None

def clean_doi(doi):
    """Convert DOI to a web-safe filename"""
    return doi.replace('/', '-').replace('.', '-')

def update_publication_pdf(pub_data, doi, pdf_path):
    """Update PDF path for matching publication in a dataset"""
    for pub in pub_data:
        if pub.get('doi') == doi:
            pub['pdf'] = pdf_path
            return True
    return False

def main():
    # Create static directory if it doesn't exist
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    # Read both YAML files
    with open("data/publications.yaml", 'r') as f:
        publications = yaml.safe_load(f)
    
    with open("data/selected_publications.yaml", 'r') as f:
        selected_publications = yaml.safe_load(f)
    
    copied_count = 0
    missing_pdfs = []
    errors = []
    
    # First, copy PDFs and update main publications
    for pub in publications:
        if 'title' not in pub or 'author' not in pub or 'year' not in pub or 'doi' not in pub:
            print(f"Warning: Publication missing required fields: {pub.get('title', 'Unknown')}")
            continue
            
        source_path = get_pdf_path(pub['title'], pub['author'], pub['year'])
        
        if source_path and os.path.exists(source_path):
            # Create filename from DOI
            safe_name = clean_doi(pub['doi']) + ".pdf"
            dest_path = os.path.join(STATIC_DIR, safe_name)
            
            try:
                shutil.copy2(source_path, dest_path)
                print(f"✓ Copied: {os.path.basename(source_path)} -> {safe_name}")
                copied_count += 1
                
                # Update PDF path in main publications
                pdf_path = f"/pub_pdfs/{safe_name}"
                pub['pdf'] = pdf_path
                
                # Update selected publications if it exists there
                update_publication_pdf(selected_publications, pub['doi'], pdf_path)
                
            except Exception as e:
                errors.append(f"Error copying {source_path}: {str(e)}")
        else:
            # Clean up the missing PDF entry
            clean_title = ' '.join(pub['title'].split())  # Remove newlines
            clean_author = re.sub(r'{highlight}|{/highlight}|\*', '', pub['author'].split(',')[0])
            clean_author = re.split(r'\s+[A-Z](\s+|[A-Z]|\.|$)', clean_author)[0]
            missing_pdfs.append(f"{clean_author} et al. {pub['year']} - {clean_title}")
    
    # Write updated YAMLs back
    print("\nWriting updated YAML files...")
    
    with open("data/publications.yaml", 'w') as f:
        yaml.dump(publications, f, default_flow_style=False, sort_keys=False)
    
    with open("data/selected_publications.yaml", 'w') as f:
        yaml.dump(selected_publications, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nResults:")
    print(f"Copied {copied_count} PDFs")
    
    if missing_pdfs:
        print(f"\nMissing PDFs ({len(missing_pdfs)}):")
        # Remove duplicates and sort
        for pdf in sorted(set(missing_pdfs)):
            print(f"- {pdf}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(error)

if __name__ == "__main__":
    main() 