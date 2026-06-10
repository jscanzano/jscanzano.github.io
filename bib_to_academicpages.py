"""
BibTeX to Academic Pages publication markdown converter
Usage: python bib_to_academicpages.py publications.bib
Outputs one .md file per entry into ./_publications/
"""

import re
import os
import sys

def parse_bibtex(bib_content):
    """Parse a BibTeX file into a list of entry dicts."""
    entries = []
    # Match each @type{key, ...} block
    pattern = re.compile(r'@(\w+)\s*\{([^,]+),\s*(.*?)\n\}', re.DOTALL)
    
    for match in pattern.finditer(bib_content):
        entry_type = match.group(1).lower()
        entry_key = match.group(2).strip()
        fields_raw = match.group(3)
        
        # Parse individual fields
        fields = {}
        field_pattern = re.compile(r'(\w+)\s*=\s*[\{\"](.+?)[\}\"],?\s*(?=\w+\s*=|\Z)', re.DOTALL)
        for field_match in field_pattern.finditer(fields_raw):
            key = field_match.group(1).lower().strip()
            value = field_match.group(2).strip()
            value = re.sub(r'\s+', ' ', value)  # collapse whitespace
            value = value.replace('{', '').replace('}', '')  # remove braces
            fields[key] = value
        
        fields['_type'] = entry_type
        fields['_key'] = entry_key
        entries.append(fields)
    
    return entries


def get_category(entry_type, fields):
    """Map BibTeX entry type to Academic Pages category."""
    if entry_type in ('article',):
        return 'manuscripts'
    elif entry_type in ('inproceedings', 'conference', 'proceedings'):
        return 'conferences'
    elif entry_type in ('phdthesis', 'mastersthesis', 'thesis'):
        return 'manuscripts'
    else:
        return 'manuscripts'


def format_authors(author_string):
    """Format author string for citation."""
    if not author_string:
        return ""
    authors = [a.strip() for a in author_string.split(' and ')]
    formatted = []
    for author in authors:
        if ',' in author:
            parts = author.split(',', 1)
            last = parts[0].strip()
            first = parts[1].strip() if len(parts) > 1 else ''
            # Abbreviate first name
            initials = ' '.join(p[0] + '.' for p in first.split() if p)
            formatted.append(f"{last}, {initials}")
        else:
            parts = author.split()
            if len(parts) >= 2:
                last = parts[-1]
                initials = ' '.join(p[0] + '.' for p in parts[:-1])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(author)
    
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]} & {formatted[1]}"
    else:
        return ', '.join(formatted[:-1]) + f", & {formatted[-1]}"


def make_slug(key, title):
    """Make a URL-safe slug from the entry key."""
    slug = key.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def entry_to_markdown(entry):
    """Convert a BibTeX entry dict to Academic Pages markdown."""
    entry_type = entry.get('_type', 'misc')
    entry_key = entry.get('_key', 'unknown')
    
    title = entry.get('title', 'Untitled').strip('"')
    authors = entry.get('author', '')
    year = entry.get('year', '')
    venue = entry.get('journal') or entry.get('booktitle') or entry.get('school') or ''
    doi = entry.get('doi', '')
    url = entry.get('url', '')
    abstract = entry.get('abstract', '')
    
    category = get_category(entry_type, entry)
    slug = make_slug(entry_key, title)
    permalink = f"/publication/{slug}"
    
    # Build date
    month = entry.get('month', '01')
    month_map = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'june': '06', 'july': '07', 'august': '08', 'september': '09',
        'october': '10', 'november': '11', 'december': '12'
    }
    month_num = month_map.get(month.lower(), '01') if month else '01'
    date = f"{year}-{month_num}-01" if year else "2024-01-01"
    
    # Build citation string
    author_formatted = format_authors(authors)
    if category == 'conferences':
        citation = f'{author_formatted} ({year}). {title}. <i>{venue}</i>.'
    else:
        citation = f'{author_formatted} ({year}). {title}. <i>{venue}</i>.'
    
    if doi:
        citation += f' https://doi.org/{doi}'
    
    # Build paperurl
    paperurl = f"https://doi.org/{doi}" if doi else (url if url else '')
    
    # Build frontmatter
    lines = ['---']
    lines.append(f'title: "{title}"')
    lines.append(f'collection: publications')
    lines.append(f'category: {category}')
    lines.append(f'permalink: {permalink}')
    lines.append(f'date: {date}')
    lines.append(f'venue: "{venue}"')
    if paperurl:
        lines.append(f'paperurl: "{paperurl}"')
    lines.append(f"citation: '{citation}'")
    lines.append('---')
    
    if abstract:
        lines.append('')
        lines.append(abstract)
    
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python bib_to_academicpages.py publications.bib")
        sys.exit(1)
    
    bib_file = sys.argv[1]
    
    if not os.path.exists(bib_file):
        print(f"Error: {bib_file} not found")
        sys.exit(1)
    
    with open(bib_file, 'r', encoding='utf-8') as f:
        bib_content = f.read()
    
    entries = parse_bibtex(bib_content)
    
    if not entries:
        print("No entries found in BibTeX file.")
        sys.exit(1)
    
    os.makedirs('_publications', exist_ok=True)
    
    count = 0
    for entry in entries:
        md_content = entry_to_markdown(entry)
        slug = make_slug(entry['_key'], entry.get('title', ''))
        filename = f"_publications/{slug}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"Created: {filename}")
        count += 1
    
    print(f"\nDone! Created {count} publication files in _publications/")


if __name__ == '__main__':
    main()
