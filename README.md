#Goodman Lab Website

This is the repository for the Goodman Lab website, built using [Hugo](https://gohugo.io/) - a fast and modern static site generator. The site uses the [Hugo Scroll](https://github.com/zjedi/hugo-scroll) theme for its single-page scrolling design.

## Website Structure

The main content of the website is written in Markdown files located in:
- `content/homepage/` - Contains the main sections of the homepage
- `content/` - Contains any additional standalone pages

Key configuration files:
- `hugo.toml` - Main configuration file for the website
- `static/` - Directory for images and other static files
- `layouts/` - Custom layout templates (if any)

## Local Development

### Prerequisites
1. Install Hugo (Extended version) from https://gohugo.io/installation/
   - On Mac: `brew install hugo`
   - On Windows: `choco install hugo-extended`
   - On Linux: `sudo snap install hugo`

### Running Locally
1. Clone this repository:

```bash
git clone --recursive https://github.com/dbg-lab/dbg-lab.github.io.git
cd dbg-lab.github.io
```

2. Start the local development server:

```bash
hugo server -D
```

3. View the site at http://localhost:1313/

The site will automatically update as you make changes to the content.

## Editing Content

### Main Sections
To edit the main sections of the website, modify the Markdown files in `content/homepage/`. Each section is a separate file, for example:
- `opener.md` - Welcome section
- `contact.md` - Contact information
- `publications.md` - Publications list

### Adding New Sections
1. Create a new Markdown file in `content/homepage/`
2. Include the following front matter at the top:

```yaml
---
title: "Your Section Title"
weight: 5 # Controls order on page (higher numbers appear lower)
header_menu: true # Include in navigation menu
---
```

3. Add the section content below the front matter.

### Managing Publications

The website's publication list is automatically generated from structured data files:

1. Source files:
- `cv/bib/citations.bib` - BibTeX database of publications for the lab, linked from dbg's CV repo

2. Data files (generated):
- `data/publications.yaml` - Complete publication list
- `data/selected_publications.yaml` - Curated list of highlighted publications

#### Publication Update Process

1. Add new publications to `cv/bib/citations.bib` in BibTeX format
2. Run the publication conversion scripts in order:

```bash
./scripts/bib_to_yaml.py cv/bib/citations.bib ../data/publications.yaml # Converts CV bibtex to YAML
./scripts/select_publications.py ../data/publications.yaml ../data/selected_publications.yaml # Creates selected pubs
```
3. The publications will automatically appear on the website through the `publications` shortcode:
```html
{{< publications >}} # Displays all publications
{{< selected-publications >}} # Displays only selected publications
```

#### Publication Display Options

Publications can be customized in the YAML files with the following fields:
- `pdf`: Link to PDF file (stored in `static/pub_pdfs/`)
- `doi`: DOI identifier for automatic linking
- `highlight`: Highlights author name (used for lab members)
- `selected`: Marks publication for inclusion in selected publications list

For detailed examples of the YAML format, see the existing entries in `data/publications.yaml`.

## Deployment
The site automatically deploys to GitHub Pages when changes are pushed to the main branch. Please make sure to pull the latest changes from the main branch before pushing any changes and let dbg know if you're making any changes to the website.


## Additional Resources
- [Hugo Documentation](https://gohugo.io/documentation/)
- [Hugo Scroll Theme Documentation](https://github.com/zjedi/hugo-scroll#readme)
- [Markdown Guide](https://www.markdownguide.org/basic-syntax/)

## Need Help?
Contact [lab admin](mailto:lab-admin@dbg-lab.org) for assistance with website maintenance and updates. 


