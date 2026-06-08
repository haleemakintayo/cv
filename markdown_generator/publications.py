# Publications markdown generator for AcademicPages
# 
# Takes a TSV / CSV of publications with metadata and converts them for use with [academicpages.github.io](academicpages.github.io). 
# Can be called via the command prompt by using `python3 publications.py [filename]`.

# Data format
# 
# The file needs to have the following columns as a header at the top:
# pub_date, title, venue, excerpt, citation, url_slug, paper_url, slides_url
# - `excerpt`, `paper_url`, and slides_url can be blank, but the others must have values. 
# - `pub_date` must be formatted as YYYY-MM-DD.
# - `url_slug` will be the descriptive part of the .md file and the permalink URL for the page about the paper. 
#    The .md file will be `YYYY-MM-DD-[url_slug].md` and the permalink will be `https://[yourdomain]/publications/YYYY-MM-DD-[url_slug]`
import csv
import os
import sys
import json
import re

# Flag to indicate an error occurred
EXIT_ERROR = 1

# The expected layout of the CSV / TSV file
HEADER_LEGACY  = ['pub_date', 'title', 'venue', 'excerpt', 'citation', 'url_slug', 'paper_url', 'slides_url']
HEADER_UPDATED = ['pub_date', 'title', 'venue', 'excerpt', 'citation', 'url_slug', 'paper_url', 'slides_url', 'category']

# YAML is very picky about how it takes a valid string, so we are replacing single and double quotes (and ampersands)
# with their HTML encoded equivalents. This makes them look not so readable in raw format, but they are parsed and
# rendered nicely.
HTML_ESCAPE_TABLE = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
    }

def slugify(text):
    """Convert title to a URL-friendly slug."""
    text = text.lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-')

# This is where the heavy lifting is done. This loops through all the rows in the TSV dataframe, then starts to
# concatenate a big string (```md```) that contains the markdown for each type. It does the YAML metadata first, then
# does the description for the individual page.
def create_md(lines: list, layout: list = None):
    for item in lines:
        # Handle dictionary (from JSON) or list (from CSV/TSV)
        if isinstance(item, dict):
            title = item.get('title', 'Untitled')
            pub_date = f"{item.get('year', '2024')}-01-01"
            venue = item.get('venue', 'Unknown Venue')
            excerpt = item.get('abstract', '')
            paper_url = item.get('link', '')
            citation = item.get('citation') or f"{item.get('authors', 'Unknown')}. ({item.get('year', '2024')}). \"{title}.\" *{venue}*."
            url_slug = slugify(title)
            category = 'manuscripts'
        else:
            pub_date = item[layout.index('pub_date')]
            title = item[layout.index('title')]
            venue = item[layout.index('venue')]
            excerpt = item[layout.index('excerpt')]
            citation = item[layout.index('citation')]
            url_slug = item[layout.index('url_slug')]
            paper_url = item[layout.index('paper_url')]
            category = item[layout.index('category')] if 'category' in layout else 'manuscripts'

        # Parse the filename information
        md_filename = f"{pub_date}-{url_slug}.md"
        html_filename = f"{pub_date}-{url_slug}"
        
        # Parse the YAML variables
        md = f"---\ntitle: \"{title}\"\n"
        md += "collection: publications\n"
        md += f"category: {category}\n"
        md += f"permalink: /publication/{html_filename}\n"
        if len(str(excerpt)) > 5:
            md += f"excerpt: '{html_escape(str(excerpt))}'\n"
        md += f"date: {pub_date}\n"
        md += f"venue: '{html_escape(str(venue))}'\n"
        if len(str(paper_url)) > 5:
            md += f"paperurl: '{paper_url}'\n"
        md += f"citation: '{html_escape(str(citation))}'\n"
        md += "---\n"
        
        # Markdown description for individual page
        if len(str(paper_url)) > 5:
            md += f"\n<a href='{paper_url}'>Download paper here</a>\n"
        if len(str(excerpt)) > 5:
            md += f"\n{html_escape(str(excerpt))}\n"
        md += f"\nRecommended citation: {citation}"
        
        # Write the file
        out_dir = "../_publications/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        md_filename = os.path.join(out_dir, os.path.basename(md_filename))
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(md)

def html_escape(text):
    """Produce entities within text."""
    return "".join(HTML_ESCAPE_TABLE.get(c,c) for c in text)

def read(filename: str) -> tuple[list, list]:
    '''Read the contents of the file, check the header and return the parsed line along with the file type.'''

    # Read the contents of the file
    lines = []
    if filename.endswith('.json'):
        with open(filename, 'r', encoding='utf-8') as file:
            lines = json.load(file)
        return lines, None

    with open(filename, 'r') as file:
        delimiter = ',' if filename.endswith('.csv') else '\t'
        reader = csv.reader(file, delimiter=delimiter)
        for row in reader:
            lines.append(row)

    # Verify the file format makes sense
    if len(lines) <= 1:
        print(f'Not enough lines in the file to process, found {len(lines)}', file=sys.stderr)
        sys.exit(EXIT_ERROR)

    # Verify the header, remove it once checked
    layout = HEADER_UPDATED
    if HEADER_LEGACY == lines[0]:
        layout = HEADER_LEGACY
    elif HEADER_UPDATED != lines[0]:
        print(lines[0])
        print('The header of the file does not match the expected format', file=sys.stderr)
        sys.exit(EXIT_ERROR)
    lines = lines[1:]
    
    # Return the lines and format
    return lines, layout

if __name__ == '__main__':
    # Make sure a filename was given
    if len(sys.argv) != 2:
        print('Usage: python3 publications.py [filename]', file=sys.stderr)
        sys.exit(EXIT_ERROR)

    # Make sure the filename is TSV or CSV
    filename = sys.argv[1]
    if not (filename.endswith('.csv') or filename.endswith('.tsv') or filename.endswith('.json')):
        print(f'Expected a TSV, CSV, or JSON file, got {filename}', file=sys.stderr)
        sys.exit(EXIT_ERROR)    

    # Read and process the lines
    lines, layout = read(filename)
    create_md(lines, layout)
