import config
import utils.parsing.parser as parser
import re
import urllib.parse

import vitd_utils.censor_pass


def page_name_to_file_name(page_name):
    path = page_name
    path = path.replace(' - ', '_')
    path = path.replace(' – ', '_')
    path = path.replace(' ', '_').replace('/', '-')
    path = path.replace('...', '_')
    path = path.replace('"', '')
    path = path.replace("'", '')
    path = path.replace(':', '_')
    path = path.replace(',', '_')
    if path[0] == '.':
        path = path[1:]
    return path


def escape_for_html(content):
    return content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def apply_text_substitutions(content):
    """Apply standard text substitutions to correct common issues.
    
    This function centralizes all text substitutions in one place,
    making it easier to add new ones in the future.
    """
    # Handle consecutive horizontal space tags by adding spaces between them
    # This prevents the parser from misinterpreting them inside color blocks
    while '~hs~~hs~' in content:
        content = content.replace('~hs~~hs~', '~hs~ ~hs~')
    
    # Bracket substitutions (conditional based on config)
    if config.REMOVE_DOUBLE_SQUARE_BRACKETS:
        while '[[' in content:
            content = content.replace('[[', '[')
        while ']]' in content:
            content = content.replace(']]', ']')

    # Fix missing right bracket in links (conditional based on config)
    if config.ADD_MISSING_BRACKET_ON_LEFT:
        # Use regex to find "__[text__" pattern and add the missing "]"
        content = re.sub(r'(__\[[^\]]*?)__', r'\1]__', content)

    # Transform displayXXXX pattern to fileId in img tags (conditional based on config)
    if config.TRANSFORM_DISPLAY_XXXX:
        # Convert {img src="displayXXXX" ...} to {img fileId="XXXX" ...}
        content = re.sub(r'\{img([^}]*?)src="display(\d+)"([^}]*?)\}', r'{img\1fileId="\2"\3}', content)

    # Too many parens
    if config.REDUCE_TRIPLE_PARENS:
        while '(((' in content:
            content = content.replace('(((', '((')
        while ')))' in content:
            content = content.replace(')))', '))')
        
    # Specific text replacements (always applied)
    # Match any case variation of "vitaminDwiki" and normalize to "VitaminDWiki"
    content = re.sub(r'[vV][iI][tT][aA][mM][iI][nN][dD][wW][iI][kK][iI]', 'VitaminDWiki', content)
    
    # Fix double equals in page_id
    if 'page_id==' in content:
        content = content.replace('page_id==', 'page_id=')

    # Fix DOI links with unwanted spaces - this specifically targets the pattern in
    # https://doi.org/10.1016/S0021- 9258(18)85783-0
    content = re.sub(r'(https?://doi\.org/[^/\s]*?)-\s+([0-9])', r'\1-\2', content)
        
    return content


# Keep for backward compatibility
def pre_censor(tiki):
    """Deprecated: Use apply_text_substitutions instead."""
    return apply_text_substitutions(tiki)


def escape_url(url):
    """Properly escape URLs with spaces and special characters.
    
    Args:
        url: A URL string that may contain spaces or special characters
        
    Returns:
        A properly escaped URL that can be used in HTML/markdown links
    """
    # Print the input URL for debugging
    print(f"DEBUG: Escaping URL: '{url}'")
    
    # First remove any extra whitespace at the beginning or end
    url = url.strip()
    
    # If the URL already appears to be encoded, don't double-encode it
    if '%20' in url or '%3A' in url:
        return url
    
    # Character-by-character encoding that preserves URL structure
    result = []
    
    # Keep track of whether we're inside a schema (e.g., http://)
    in_schema = False
    schema_buffer = ""
    
    for char in url:
        # Preserve common URL structural characters
        if char in "/:?&#=":
            # If we were building a schema, flush it
            if in_schema and char == ':':
                result.append(schema_buffer + char)
                in_schema = False
                schema_buffer = ""
            else:
                result.append(char)
        # Handle potential schema (protocol) part of URL
        elif not in_schema and len(result) == 0 and char.isalpha():
            # Might be start of schema like http:// or https://
            in_schema = True
            schema_buffer = char
        elif in_schema and (char.isalpha() or char == '.'):
            # Continue building schema
            schema_buffer += char
        elif char == " ":
            # Spaces become %20
            result.append("%20")
        elif re.match(r'[a-zA-Z0-9._~-]', char):
            # RFC 3986 unreserved characters stay as-is
            result.append(char)
        else:
            # Everything else gets percent-encoded
            result.append(urllib.parse.quote(char))
    
    # If we still have a schema buffer, add it (shouldn't happen in well-formed URLs)
    if in_schema:
        result.append(urllib.parse.quote(schema_buffer))
                
    return "".join(result)


def convert_tiki_to_md(tiki):

    # print('TIKI DATA:')
    # print(tiki)

    # print('========================')

    # Apply text substitutions before parsing
    tiki = apply_text_substitutions(tiki)

    ast = parser.parse(tiki)

    ast_str = []
    for node in ast:
        ast_str.append(parser.format_node(node))
    # ast_str = "\n".join(ast_str)
    ast_str = "".join(ast_str)
    # print('AST STR:')
    # print(ast_str)

    # TODO: 'censor' pass goes here instead? in addition?

    md = parser.render_as_markdown(ast)

    censored_sections = []
    if config.POST_CENSOR:
        md, censored_sections = vitd_utils.censor_pass.post_censor(md)

    # print('MD STR:')
    # print(md)

    if not config.DEBUG_MODE:
        return md, censored_sections
    
    # Format the output with all stages, using HTML to ensure proper rendering
    return f"""
{md}

<pre style="background-color: #e0e0e0; white-space: pre-wrap;">
<code class="language-text">
Markdown:
--------
{escape_for_html(md)}

AST Structure:
-------------
{escape_for_html(ast_str)}

Original Tiki:
-------------
{escape_for_html(tiki)}
</code>
</pre>
""", censored_sections
