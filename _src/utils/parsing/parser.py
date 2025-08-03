import os
from typing import Optional, List, Union, Tuple, Dict
import re
from pydantic import BaseModel
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Add utils to path

import conversion_config as config
import slugs
from vitd_utils.files_and_attachments import map_id_to_path
from slugs import tag_slugs_that_exist, post_slugs_that_exist, generate_post_slug, generate_hugo_tag_slug

try:
    # Try local import first (when running lr.py directly)
    from attrs import parse_attrs
except ImportError:
    # Fall back to package import (when imported from main.py)
    from parsing.attrs import parse_attrs


class BaseNode(BaseModel):
    """Base class for all nodes"""
    full_match: str
    inner_content: str

    def render(self) -> str:
        """Basic rendering that just returns text content.
        Complex nodes like LIST and TABLE will be skipped.
        No markdown formatting is applied yet."""

        if isinstance(self, TextNode):
            result = self.inner_content
            if config.DOUBLE_TEXT_NODE_NEWLINES:
                result = result.replace('\n', '\n\n')
            return result
        
        if not hasattr(self, 'full_match') or not hasattr(self, 'inner_content'):
            raise ValueError(f"Node {self.__class__.__name__} missing required fields full_match or inner_content")
            
        # certain node types are invisible
        if hasattr(self, 'flag_invisible'):
            # Instead of just returning an empty string, wrap the content in HTML comments
            # This preserves the original content in the page source while keeping it invisible in rendered output
            if config.ADD_HTML_COMMENTS_FOR_HIDDEN_NODES:
                return f"<!-- {self.full_match} -->"
            else:
                return ""

        if hasattr(self, 'flag_passthru'):
            # Render children, but ignore this wrapping node
            if not hasattr(self, 'children'):
                return ""
            rendered_children = []
            for i, child in enumerate(self.children):
                if not isinstance(child, BaseNode):
                    raise TypeError(f"Child {i} of {self.__class__.__name__} must be BaseNode, got {type(child)}")
                rendered_children.append(child.render())
            return "".join(rendered_children)

        # For nodes with children, recursively render them
        if hasattr(self, 'children'):
            if not isinstance(self.children, list):
                raise TypeError(f"Node {self.__class__.__name__} children must be list, got {type(self.children)}")
                
            rendered_children = []
            for i, child in enumerate(self.children):
                if not isinstance(child, BaseNode):
                    raise TypeError(f"Child {i} of {self.__class__.__name__} must be BaseNode, got {type(child)}")
                rendered_children.append(child.render())
            return "".join(rendered_children)

        return self.inner_content


class TextNode(BaseNode):
    pass


class EmphasisNode(BaseNode):
    children: List['Node'] = []
    # TODO: render this


class LinkNode(BaseNode):
    url: str
    children: List['Node'] = []

    def render(self) -> str:
        # Get the text content from children
        text = "".join(child.render() for child in self.children)
        
        # Extract page_id from tiki-index.php URLs
        if 'tiki-index.php?page_id=' in self.url:
            # Extract the page_id
            page_id_match = re.search(r'page_id=(\d+)', self.url)
            if not page_id_match:
                raise ValueError(f"Invalid Tiki URL format: {self.url} - Could not extract page_id")
                
            page_id = page_id_match.group(1)

            # Check if it exists in the post set first
            post_slug = slugs.generate_post_slug(text, enforce_unique=False)
            if post_slug in post_slugs_that_exist:
                return f"[{text}](/posts/{post_slug})"
            else:  # we ASSUME existence of tags to avoid circular discovery reference problems
                tag_slug = generate_hugo_tag_slug(text)
                return f"[{text}](/tags/{tag_slug}.html)"
        
        # Check if this is a valid URL (contains a slash) or starts with tiki-index
        if '/' in self.url or self.url.startswith('tiki-index') or self.url.startswith('https://'):
            # Copy URL to escaped_url to work with
            escaped_url = self.url
            
            # For Tiki URLs without a domain, add the domain
            if escaped_url.startswith('tiki-index') and not escaped_url.startswith('https://'):
                escaped_url = f"https://vitamindwiki.com/{escaped_url}"
            
            # Only encode spaces - the essential URL components should be preserved
            if ' ' in escaped_url:
                escaped_url = escaped_url.replace(' ', '%20')
            
            # Standard markdown link syntax: [text](url)
            return f"[{text}]({escaped_url})"
        
        # Check if this is a citation reference (digits with optional commas/asterisks)
        if re.match(r'^\d+(?:\s*[,*]\s*\d+)*$', self.url):
            # Render as superscript citation
            return f"<sup>[{self.url}]</sup>"
        
        # Otherwise, treat as normal text in brackets that should be preserved
        # Use HTML span to prevent markdown parsing inside
        return f"<span>[{self.url}]</span>"


class DivNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []
    flag_passthru: bool = True


class ListNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []
    flag_invisible: bool = True
    flag_no_parse: bool = True

    def render(self) -> str:
        return '{LIST()}'  # just so we can remove


class TableNode(BaseNode):
    children: List['Node'] = []
    
    def render(self) -> str:
        """Render table with proper markdown formatting"""
        if not self.children:
            return ""
            
        # Start with newline for clean table formatting
        result = ["\n"]
        
        # Process first row to determine column count
        if not isinstance(self.children[0], TableRowNode):
            raise ValueError(f"Table child must be TableRowNode, got {type(self.children[0])}")
        first_row = self.children[0]
        num_columns = len(first_row.children)

        if config.NO_TABLE_HEADERS:
            # Add empty header row
            result.append("|" + "|".join([" " for _ in range(num_columns)]) + "|\n")

            # Add header separator row
            result.append("|" + "|".join([" --- " for _ in range(num_columns)]) + "|\n")

            result.append(first_row.render())
        else:
        
            # Add first row
            result.append(first_row.render())

            # Add header separator row
            result.append("|" + "|".join([" --- " for _ in range(num_columns)]) + "|\n")
        
        # Process remaining rows
        for row in self.children[1:]:
            if not isinstance(row, TableRowNode):
                raise ValueError(f"Table child must be TableRowNode, got {type(row)}")
            result.append(row.render())
            
        # End with newline
        result.append("\n")
        return "".join(result)


class ImgNode(BaseNode):
    attrs_dict: Dict[str, str]
    
    def render(self) -> str:
        """Render image tag using map_id_to_path to get the image path.
        
        Examples:
            {img type="attId" attId="21139" width="400"} becomes <img src="/path/to/image.jpg" alt="image" width="400">
            {img type="src" src="https://example.com/image.jpg"} becomes <img src="https://example.com/image.jpg" alt="image">
            {img attId="123,456,789" height="250"} becomes multiple images in sequence
            
        Raises:
            ValueError: If attachment ID is missing in the attributes.
        """
        # Extract other potential attributes for the image
        alt_text = self.attrs_dict.get('alt', 'image')
        width = self.attrs_dict.get('width', '')
        height = self.attrs_dict.get('height', '')
        
        # Check if this is a direct src URL
        if 'src' in self.attrs_dict:
            # Use the src directly for external URLs
            src_path = self.attrs_dict.get('src')
            # Create HTML img tag and add width/height attributes if provided
            width_attr = f' width="{width}"' if width else ''
            height_attr = f' height="{height}"' if height else ''
            return f'<img src="{src_path}" alt="{alt_text}"{width_attr}{height_attr}>'
        else:
            # Process attachment IDs
            result_images = []
            
            # Helper function to process a single ID
            def process_id(id_type, id_value):
                try:
                    # If the ID contains commas, it's multiple images
                    if ',' in id_value:
                        # Split by comma and process each ID
                        id_list = [id.strip() for id in id_value.split(',')]
                        # print(f"Processing multiple IDs: {id_list}")
                        
                        for single_id in id_list:
                            if single_id:  # Skip empty IDs
                                try:
                                    id = _parse_numeric_id(single_id)
                                    attachment_path = map_id_to_path(id_type, id, 'img')
                                    width_attr = f' width="{width}"' if width else ''
                                    height_attr = f' height="{height}"' if height else ''
                                    result_images.append(f'<img src="{attachment_path}" alt="{alt_text}"{width_attr}{height_attr}>')
                                except ValueError as e:
                                    print(f"WARNING: Skipping invalid ID in list: '{single_id}', Error: {str(e)}")
                    else:
                        # Process single ID
                        id = _parse_numeric_id(id_value)
                        attachment_path = map_id_to_path(id_type, id, 'img')
                        width_attr = f' width="{width}"' if width else ''
                        height_attr = f' height="{height}"' if height else ''
                        result_images.append(f'<img src="{attachment_path}" alt="{alt_text}"{width_attr}{height_attr}>')
                except ValueError as e:
                    # Print diagnostic information before re-raising
                    print(f"ERROR: Failed to parse {id_type}: '{id_value}', full attrs: {self.attrs_dict}")
                    # Enhanced error with the raw ID value and original error
                    raise ValueError(f"Invalid {id_type} format: '{id_value}'. Error: {str(e)}") from e
            
            # Try different ID attributes in order of preference
            # TODO asdfasdf handle correctly for file vs attachment
            if 'attId' in self.attrs_dict:
                process_id('attId', self.attrs_dict.get('attId'))
            elif 'fileId' in self.attrs_dict:
                process_id('fileId', self.attrs_dict.get('fileId'))
            elif 'id' in self.attrs_dict:
                process_id('id', self.attrs_dict.get('id'))
            else:
                # Throw exception for missing ID
                raise ValueError(f"Missing attachment ID or src in image node: {self.attrs_dict}")
            
            # Join all images together
            return '\n'.join(result_images)


class HeadingNode(BaseNode):
    level: int  # Number of ! characters
    children: List['Node'] = []

    def render(self) -> str:
        # Convert from Tiki's ! level to markdown # level
        # Add a newline after the heading for proper markdown formatting
        hashes = '#' * self.level
        content = ''.join(child.render() for child in self.children)
        return f"\n{hashes} {content}\n"


class MakeTocNode(BaseNode):
    attrs_dict: Dict[str, str]

    def render(self) -> str:
        """Directly output Hugo TableOfContents HTML
        
        Using raw HTML syntax to output the Hugo template code for TableOfContents.
        This will only appear where {maketoc} tags were used in the original content.
        """
        if config.RENDER_TOC:
            # return '{{ .TableOfContents }}'
            return '{{< toc >}}'
        else:
            return ''


class BoldNode(BaseNode):
    children: List['Node'] = []

    def render(self) -> str:
        stripped_content = ''.join(child.render() for child in self.children).strip()
        return f" **{stripped_content}** "


class ListItemNode(BaseNode):
    depth: int  # Number of * at start
    children: List['Node'] = []

    def render(self) -> str:
        # Add 2 spaces per depth level, then the * marker
        indent = "   " * (self.depth - 1)  # -1 because depth 1 has no indent. also need 3 spaces, not two
        marker = f"{indent}* "
        
        # Render children and join with empty string (no extra spaces between inline elements)
        content = "".join(child.render() for child in self.children)
        
        return marker + content


class NumListItemNode(BaseNode):
    depth: int  # Number of * at start
    children: List['Node'] = []

    def render(self) -> str:
        # Add 2 spaces per depth level, then the * marker
        indent = "  " * (self.depth - 1)  # -1 because depth 1 has no indent
        marker = f"{indent}1. "

        # Render children and join with empty string (no extra spaces between inline elements)
        content = "".join(child.render() for child in self.children)

        return marker + content


class IncludeNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []

    def render(self) -> str:
        return '{include}'  # just so we can remove


class LocalLinkNode(BaseNode):
    page: str = ""  # Name of the linked page
    children: List['Node'] = []

    def render(self) -> str:
        # For local links, we'll use relative paths in the Hugo site
        post_slug = slugs.generate_post_slug(self.page, enforce_unique=False)

        # The text is either the children content or the page name if no children
        text = "".join(child.render() for child in self.children) if self.children else self.page

        if post_slug in post_slugs_that_exist:
            return f"[{text}](/posts/{post_slug})"
        else:  # we ASSUME existence of tags to avoid circular discovery reference problems
            tag_slug = slugs.generate_hugo_tag_slug(self.page)              
            return f"[{text}](/tags/{tag_slug}.html)"

class AliasedLocalLinkNode(BaseNode):
    """Node for local links with aliases like ((page name|display text))"""
    page: str = ""
    display_text: str = ""
    children: List['Node'] = []

    def render(self) -> str:
        # For local links, we'll use relative paths in the Hugo site
        post_slug = slugs.generate_post_slug(self.page, enforce_unique=False)
        
        # Use the explicit display text for the link text
        text = self.display_text
        
        if post_slug in post_slugs_that_exist:
            return f"[{text}](/posts/{post_slug})"
        else:  # we ASSUME existence of tags to avoid circular discovery reference problems
            tag_slug = generate_hugo_tag_slug(text)
            return f"[{text}](/tags/{tag_slug}.html)"


class AttachNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []

    def render(self) -> str:
        assert 'id' in self.attrs_dict, 'missing id'
        # Extract the ID from attrs_dict
        # TODO: asdfasdf handle this correctly (file vs attachment)
        id = int(self.attrs_dict.get('id'))
        attachment_type = 'pdf'  # TODO: this is an assumption that we will not hardcode later
        attachment_path = map_id_to_path('id', id, attachment_type)
        text = "".join(child.render() for child in self.children) if self.children else self.inner_content
        
        # Use span elements with Font Awesome classes inside MD link
        # This keeps the link in Markdown format while adding an icon via HTML
        # TODO: asdfasdf handle multiple file types here
        icon_html = '<i class="fas fa-file-pdf" style="margin-right: 0.3em;"></i>'
        # return f'{icon_html}[{text}]({attachment_path})'
        return f'{icon_html}<a href="{attachment_path}">{text}</a>'


class HorizontalSpaceNode(BaseNode):
    """Node for horizontal space"""
    repetitions: int = 1

    def render(self) -> str:
        return "&nbsp;" * self.repetitions


class HorizontalSpaceAltNode(BaseNode):
    """Node for alternative horizontal space syntax ~hshs~"""
    repetitions: int = 1

    def render(self) -> str:
        return "&nbsp;" * self.repetitions


class TikiCommentNode(BaseNode):
    """Node for Tiki comments that should be hidden from output"""
    children: List['Node'] = []
    flag_invisible: bool = True


class FontNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []


class NewlineNode(BaseNode):
    def render(self) -> str:
        return "  \n"  # needs the two trailing spaces to make a new lines


class FadeNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []


class ItalixNode(BaseNode):
    children: List['Node'] = []


class ListPagesNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []

    def render(self) -> str:
        return '{LISTPAGES}'  # just so we can remove


class CategoryNode(BaseNode):
    attrs_dict: Dict[str, str]

    def render(self) -> str:
        return '{category}'  # just so we can remove


class FilterNode(BaseNode):
    attrs_dict: Dict[str, str]
    flag_invisible: bool = True


class BoxNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []
    
    def render(self) -> str:
        """Render a box with its content and styling.
        
        Examples:
            {BOX(bg=>#FFFAE2,width="800px")} content {BOX} becomes 
            <div style="background-color:#FFFAE2;width:800px;">content</div>
        """
        # Extract styling attributes
        style_attrs = []
        
        # Default styling for light grey background and padding/margin
        style_attrs.append("background-color:#f5f5f5")  # Light grey background
        style_attrs.append("padding:15px")
        style_attrs.append("margin:10px 0")
        style_attrs.append("border-radius:5px")
        
        # Process custom styling attributes (will override defaults if specified)
        if 'bg' in self.attrs_dict:
            bg_color = self.attrs_dict['bg'].lstrip('>')  # Remove leading '>' if present
            style_attrs[0] = f"background-color:{bg_color}"  # Override default background
        
        if 'width' in self.attrs_dict:
            width_value = self.attrs_dict['width'].strip('"\'')  # Remove quotes
            style_attrs.append(f"width:{width_value}")
            
        if 'height' in self.attrs_dict:
            height_value = self.attrs_dict['height'].strip('"\'')
            style_attrs.append(f"height:{height_value}")
            
        if 'padding' in self.attrs_dict:
            padding_value = self.attrs_dict['padding'].strip('"\'')
            style_attrs[1] = f"padding:{padding_value}"  # Override default padding
            
        if 'margin' in self.attrs_dict:
            margin_value = self.attrs_dict['margin'].strip('"\'')
            style_attrs[2] = f"margin:{margin_value}"  # Override default margin
            
        if 'class' in self.attrs_dict:
            css_class = f' class="{self.attrs_dict["class"]}"'
        else:
            css_class = ""
            
        # Combine all style attributes
        style_attr = f' style="{";".join(style_attrs)}"'
        
        # Process inner content - for now, just use inner_content
        # Later we can properly parse the children if needed
        if self.children:
            content = "".join(child.render() for child in self.children)
        else:
            # If for some reason children weren't populated correctly,
            # fall back to inner_content (defensive programming)
            content = self.inner_content
        
        # Return div with appropriate styling
        return f'<div{css_class}{style_attr}>{content}</div>'


class NoParseNode(BaseNode):
    children: List['Node'] = []
    flag_no_parse: bool = True


class HtmlNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []
    flag_no_parse: bool = True


class AlinkNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []


class ColorNode(BaseNode):
    attrs_dict: Dict[str, str]
    children: List['Node'] = []

    def render(self) -> str:
        # Render the child content
        text = "".join(child.render() for child in self.children)

        # only render color stuff IF all children are simple text nodes
        all_text = True
        for child in self.children:
            if not isinstance(child, TextNode):
                # Not all children are TextNodes
                all_text = False
                break
        if not all_text:
            return text

        # need to replace asterisks as this can break the Hugo parser
        if config.REPLACE_ASTERISKS_INSIDE_HTML:
            text = text.replace('*', config.ASTERISK_REPLACEMENT)
        
        # Use raw_content for the color specification
        color_spec = self.attrs_dict.get('raw_content', 'orange')
        
        # Check if we have both foreground and background colors
        if ',' in color_spec:
            fg_color, bg_color = color_spec.split(',', 1)
            return f'<span style="color:{fg_color};background-color:{bg_color};">{text}</span>'
        else:
            # Just foreground color
            return f'<span style="color:{color_spec};">{text}</span>'


class IndentNode(BaseNode):
    level: int = 0  # Number of + characters
    children: List['Node'] = []
    
    def render(self) -> str:
        # Render indentation using non-breaking spaces
        # Each level adds 4 non-breaking spaces
        content = "".join(child.render() for child in self.children)
        # indentation = "&nbsp;" * (self.level * 4)  # 4 spaces per level
        indentation = "> " * self.level
        
        # Simply prepend the indentation to the content
        return f'{indentation}{content}'


class WeirdCitationNode(BaseNode):
    """Node for weird citation format like [[123]"""
    citation: str
    had_space: bool = False  # Flag to track if there was a leading space

    def render(self) -> str:
        return f"<sup>[{self.citation}]</sup>"


class RedirectNode(BaseNode):
    attrs_dict: Dict[str, str]


class TableRowNode(BaseNode):
    """A row within a table, contains TableCell nodes"""
    children: List['Node'] = []
    
    def render(self) -> str:
        """Render row with proper cell separation"""
        if not self.children:
            return ""
            
        result = []
        for cell in self.children:
            if not isinstance(cell, TableCellNode):
                raise ValueError(f"TableRow child must be TableCellNode, got {type(cell)}")
            result.append(cell.render())
        
        # End row with pipe and newline
        return "".join(result) + "|\n"


class TableCellNode(BaseNode):
    """A cell within a table row, can contain any inline formatting"""
    children: List['Node'] = []
    
    def render(self) -> str:
        """Render cell with proper markdown table formatting"""
        # Start cell with pipe and space
        result = ["| "]
        
        # Render all child content
        for child in self.children:
            # Special handling for newlines in cells
            if isinstance(child, NewlineNode):
                result.append("<br>")
            else:
                result.append(child.render())
                
        # Add trailing space but no pipe (pipe added by row)
        result.append(" ")
        return "".join(result)


class HorizontalRuleNode(BaseNode):
    def render(self) -> str:
        return "\n\n---\n\n"


class HorizontalRuleAltNode(BaseNode):
    def render(self) -> str:
        return "\n\n---\n\n"


class SqlNode(BaseNode):
    """Node for SQL queries - these should be omitted from markdown output but preserved in HTML comments"""
    attrs_dict: Dict[str, str]
    flag_invisible: bool = True


class CustomSearchNode(BaseNode):
    """Node for CUSTOMSEARCH blocks - these should be omitted from markdown output but preserved in HTML comments"""
    attrs_dict: Dict[str, str]
    children: List['Node'] = []
    flag_invisible: bool = True


class DoiLinkNode(BaseNode):
    """Node for DOI references that should be converted to proper DOI links"""
    doi: str
    
    def render(self) -> str:
        """Convert DOI reference to a proper DOI link while preserving original text
        
        Examples:
            "doi: 10.1007/s11912-023-01476-4" becomes 
            "[doi: 10.1007/s11912-023-01476-4](https://doi.org/10.1007/s11912-023-01476-4)"
        """
        # Remove any leading/trailing whitespace from the DOI
        clean_doi = self.doi.strip()
        url = f"https://doi.org/{clean_doi}"
        # Use the original match as the link text
        return f"[{self.full_match}]({url})"


class SupNode(BaseNode):
    """Node for superscript text like {SUP()}1,{SUP} or {SUP()}5{SUP}"""
    attrs_dict: Dict[str, str]
    children: List['Node'] = []
    
    def render(self) -> str:
        """Render superscript text with HTML <sup> tags
        
        Examples:
            {SUP()}1,{SUP} becomes <sup>1,</sup>
            {SUP()}5{SUP} becomes <sup>5</sup>
        """
        if not self.children:
            raise Exception('expected children')
            
        rendered_children = []
        for child in self.children:
            rendered_children.append(child.render())
        
        inner_content = ''.join(rendered_children)
        # Safe HTML output using sup tags
        return f"<sup>{inner_content}</sup>"


class ImgBlockNode(BaseNode):
    attrs_dict: Dict[str, str]
    inner_content: str  # This might be empty for most cases
    
    def render(self) -> str:
        """Render block form image tag using map_id_to_path to get the image path.
        
        Examples:
            {IMG(attId="22584" max="400")}{IMG} becomes <img src="/path/to/image.jpg" alt="image" max="400">
            
        Raises:
            ValueError: If attachment ID is missing in the attributes.
        """
        # Extract other potential attributes for the image
        alt_text = self.attrs_dict.get('alt', 'image')
        width = self.attrs_dict.get('width', '')
        height = self.attrs_dict.get('height', '')
        max_width = self.attrs_dict.get('max', '')  # Support for max attribute
        
        # Check if this is a direct src URL
        if 'src' in self.attrs_dict:
            # Use the src directly for external URLs
            src_path = self.attrs_dict.get('src')
            # Create HTML img tag and add width/height/max attributes if provided
            width_attr = f' width="{width}"' if width else ''
            height_attr = f' height="{height}"' if height else ''
            max_attr = f' style="max-width: {max_width}px;"' if max_width else ''
            return f'<img src="{src_path}" alt="{alt_text}"{width_attr}{height_attr}{max_attr}>'
        else:
            # Process attachment IDs
            result_images = []
            
            # Try different ID attributes in order of preference
            if 'attId' in self.attrs_dict:
                id_type = 'attId'
                id_value = self.attrs_dict.get('attId')
            elif 'fileId' in self.attrs_dict:
                id_type = 'fileId'
                id_value = self.attrs_dict.get('fileId')
            elif 'id' in self.attrs_dict:
                id_type = 'id'
                id_value = self.attrs_dict.get('id')
            else:
                # Throw exception for missing ID
                raise ValueError(f"Missing attachment ID or src in image block node: {self.attrs_dict}")
            
            try:
                # If the ID contains commas, it's multiple images
                if ',' in id_value:
                    # Split by comma and process each ID
                    id_list = [id.strip() for id in id_value.split(',')]
                    # print(f"Processing multiple IDs in block: {id_list}")
                    
                    for single_id in id_list:
                        if single_id:  # Skip empty IDs
                            try:
                                id = _parse_numeric_id(single_id)
                                attachment_path = map_id_to_path(id_type, id, 'img')
                                width_attr = f' width="{width}"' if width else ''
                                height_attr = f' height="{height}"' if height else ''
                                max_attr = f' style="max-width: {max_width}px;"' if max_width else ''
                                result_images.append(f'<img src="{attachment_path}" alt="{alt_text}"{width_attr}{height_attr}{max_attr}>')
                            except ValueError as e:
                                print(f"WARNING: Skipping invalid ID in list: '{single_id}', Error: {str(e)}")
                else:
                    # Process single ID
                    id = _parse_numeric_id(id_value)
                    attachment_path = map_id_to_path(id_type, id, 'img')
                    width_attr = f' width="{width}"' if width else ''
                    height_attr = f' height="{height}"' if height else ''
                    max_attr = f' style="max-width: {max_width}px;"' if max_width else ''
                    result_images.append(f'<img src="{attachment_path}" alt="{alt_text}"{width_attr}{height_attr}{max_attr}>')
            except ValueError as e:
                # Print diagnostic information before re-raising
                print(f"ERROR: Failed to parse {id_type}: '{id_value}', full attrs: {self.attrs_dict}")
                # Enhanced error with the raw ID value and original error
                raise ValueError(f"Invalid {id_type} format in block: '{id_value}'. Error: {str(e)}") from e
            
            # Join all images together
            return '\n'.join(result_images)


Node = Union[
    'TextNode',
    'EmphasisNode', 
    'LinkNode',
    'DivNode',
    'ListNode',
    'TableNode',
    'TableRowNode',
    'TableCellNode',
    'ImgNode',
    'HeadingNode',
    'MakeTocNode',
    'BoldNode',
    'ListItemNode',
    'NumListItemNode',
    'IncludeNode',
    'LocalLinkNode',
    'AliasedLocalLinkNode',  # Add the new node type
    'AttachNode',
    'HorizontalSpaceNode',
    'HorizontalSpaceAltNode',
    'TikiCommentNode',
    'FontNode',
    'NewlineNode',
    'FadeNode',
    'ItalixNode',
    'ListPagesNode',
    'CategoryNode',
    'FilterNode',
    'BoxNode',
    'NoParseNode',
    'HtmlNode',
    'AlinkNode',
    'ColorNode',
    'IndentNode',
    'WeirdCitationNode',
    'RedirectNode',
    'HorizontalRuleNode',
    'HorizontalRuleAltNode',
    'SqlNode',
    'CustomSearchNode',
    'DoiLinkNode',
    'SupNode',  # Added SupNode
    'ImgBlockNode'  # Add ImgBlockNode
]


@dataclass
class Pattern:
    """Base class for all patterns"""
    regex: str
    description: str = ""
    
    def __post_init__(self):
        self.compiled = re.compile(self.regex)
        
    def try_match(self, text: str, pos: int) -> Optional[Tuple[Node, int]]:
        """Try to match pattern at given position
        Returns (Node, new_position) if match, None if no match"""
        match = self.compiled.match(text, pos)
        if not match:
            return None

        # Get all captured groups (if any)
        captures = [match.group(i) for i in range(1, match.lastindex + 1)] if match.lastindex else []
        full_text = match.group(0)
        node, new_pos = self.create_node(full_text, captures), match.end()
        return node, new_pos
    
    def create_node(self, full_text: str, captures: List[str]) -> Node:
        """Need to override create_node"""
        raise NotImplementedError


class DivPattern(Pattern):
    """Pattern for DIV tags like {DIV}content{/DIV} or {DIV(class="...")}content{DIV}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{DIV([^}]*)\}(.*?)\{/?DIV\}',  # Note the /? for optional slash
            "DIV tag like {DIV}content{/DIV} or {DIV}content{DIV}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> DivNode:
        return DivNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class ListPattern(Pattern):
    """Pattern for {LIST()} ... {LIST} or {/LIST} blocks"""
    def __init__(self):
        super().__init__(
            r'(?s)\{LIST\((.*?)\)\}(.*?)\{(?:/)?LIST\}',  # Make / optional
            "LIST block like {LIST()}...{LIST} or {LIST()}...{/LIST}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ListNode:
        return ListNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class TablePattern(Pattern):
    """Pattern for tables like ||col1|col2||col3|col4|| or multiline tables"""
    def __init__(self):
        super().__init__(
            r'(?sm)\|\|(.*?)\|\|(?=\s*\n|\s*\Z)',  # Optional whitespace then newline, OR whitespace until end of text
            "Table like ||col1|col2||col3|col4|| or multiline"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> TableNode:
        return TableNode(
            full_match=full_text,
            inner_content=captures[0],
            children=[]
        )


class ImgPattern(Pattern):
    # TODO asdfasdf is it true that always an attId?
    """Pattern for image tags like {img type="attId" attId="21139" width="400"}"""
    def __init__(self):
        super().__init__(
            r'\{img([^}]+)\}',  # Capture everything between {img and } as attributes
            "Image tag like {img type=\"attId\" attId=\"21139\"}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ImgNode:
        return ImgNode(
            full_match=full_text,
            inner_content='',
            attrs_dict=parse_attrs(captures[0])
        )


class LinkPattern(Pattern):
    """Pattern for links like [url|link]"""
    def __init__(self):
        super().__init__(
            r'\[(?P<url>[^|\]]+?)\|(?P<text>[^\]]+?)\]',  # Non-greedy matches
            "Link with text like [url|link]"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> LinkNode:
        return LinkNode(
            full_match=full_text,
            inner_content=captures[1],
            url=captures[0],
            children=[]  # Will be populated in parse_link_node
        )


class BoldPattern(Pattern):
    """Pattern for bold text like __text__ (can span multiple lines)"""
    def __init__(self):
        super().__init__(
            r'(?s)__(.*?)__',  # (?s) to allow matching across lines
            "Bold text like __bold__ (can span multiple lines)"
        )

    def create_node(self, full_text: str, captures: List[str]) -> BoldNode:
        return BoldNode(
            full_match=full_text,
            inner_content=captures[0],
            children=[]
        )


class EmphasisPattern(Pattern):
    """Pattern for emphasized text like ''text'' (can span multiple lines)"""
    def __init__(self):
        super().__init__(
            r"(?s)''(.*?)''",  # (?s) to allow matching across lines
            "Emphasized text like ''italic'' (can span multiple lines)"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> EmphasisNode:
        return EmphasisNode(
            full_match=full_text,
            inner_content=captures[0],
            children=[]  # Will be populated by parsing match.group(1)
        )


class HeadingPattern(Pattern):
    """Pattern for headings like !Title or !!Subtitle at start of line"""
    def __init__(self):
        super().__init__(
            r'\n?(!+)[ \t]*(.*?)[ \t]*(?=\n|$)',  # Optional leading newline, optional whitespace
            "Heading like !Title or !!Subtitle at start of line"
        )
    
    def try_match(self, text: str, pos: int) -> Optional[Tuple[Node, int]]:
        """Override try_match to ensure we're at start of line"""
        # Check if we're at start of line (pos == 0 or previous char is newline)
        if pos > 0 and text[pos-1] != '\n':
            return None
        return super().try_match(text, pos)
    
    def create_node(self, full_text: str, captures: List[str]) -> HeadingNode:
        return HeadingNode(
            full_match=full_text,
            inner_content=captures[1].strip(),  # Content after !s, stripped
            level=len(captures[0]),  # Number of ! chars
            children=[]  # Will be populated by parsing content
        )


class MakeTocPattern(Pattern):
    """Pattern for {maketoc Title=""}"""
    def __init__(self):
        super().__init__(
            r'\{maketoc([^}]*)\}',
            "Table of contents marker"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> MakeTocNode:
        return MakeTocNode(
            full_match=full_text,
            inner_content='',
            attrs_dict=parse_attrs(captures[0])
        )


class ListItemPattern(Pattern):
    """Pattern for list items like * or ** at start of line"""
    def __init__(self):
        super().__init__(
            r'(?m)^(\*+)(.+?)(?=\n|$)',  # (?m) for multiline mode, match * at start of line
            "List item like * or ** at start of line"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ListItemNode:
        return ListItemNode(
            full_match=full_text,
            inner_content=captures[1],
            depth=len(captures[0]),  # Number of * chars
            children=[]  # Will be populated in parse_list_item
        )


class NumListItemPattern(Pattern):
    """Pattern for list items like * or ** at start of line"""

    def __init__(self):
        super().__init__(
            r'(?m)^(#+)(.+?)(?=\n|$)',  # (?m) for multiline mode, match * at start of line
            "Num List item like # or ## at start of line"
        )

    def create_node(self, full_text: str, captures: List[str]) -> NumListItemNode:
        return NumListItemNode(
            full_match=full_text,
            inner_content=captures[1],
            depth=len(captures[0]),  # Number of * chars
            children=[]  # Will be populated in parse_list_item
        )


class IncludePattern(Pattern):
    """Pattern for including other pages like {include page="pagename"}"""
    def __init__(self):
        super().__init__(
            r'\{include([^}]+)\}',  # Capture all attributes
            "Include directive like {include page=\"pagename\"}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> IncludeNode:
        return IncludeNode(
            full_match=full_text,
            inner_content='',
            attrs_dict=parse_attrs(captures[0]),
            children=[]  # Will be populated if/when we parse included content
        )


class AliasedLocalLinkPattern(Pattern):
    """Pattern for local links with aliases like ((page name|display text))"""
    def __init__(self):
        super().__init__(
            r'\(\((?P<page>[^|]+?)\|(?P<text>.+?)\)\)',  # Match ((page|text)) format exactly
            "Local link with alias like ((page name|display text))"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> AliasedLocalLinkNode:
        page_name = captures[0].strip()
        display_text = captures[1].strip()
        
        return AliasedLocalLinkNode(
            full_match=full_text,
            inner_content=f"{page_name}|{display_text}",
            page=page_name,
            display_text=display_text,
            children=[]
        )


class LocalLinkPattern(Pattern):
    """Pattern for local links like ((page name))"""
    def __init__(self):
        super().__init__(
            r'\(\((.*?)\)\)',  # Match content between (( and ))
            "Local link like ((page name))"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> LocalLinkNode:
        return LocalLinkNode(
            full_match=full_text,
            inner_content=captures[0],
            page=captures[0],  # TODO: why?.strip(),  # Remove any whitespace from page name
            children=[]
        )


class AttachPattern(Pattern):
    """Pattern for ATTACH tags like {ATTACH(inline="1" id="22000" icon="1")}content{ATTACH}"""

    def __init__(self):
        super().__init__(
            r'(?s)\{ATTACH([^}]*)\}(.*?)\{/?ATTACH\}',  # Note the /? for optional slash
            "ATTACH tag like {ATTACH}content{/ATTACH} or {ATTACH}content{ATTACH}"
        )

    def create_node(self, full_text: str, captures: List[str]) -> AttachNode:
        return AttachNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class HorizontalSpacePattern(Pattern):
    """Pattern for horizontal space markers like ~hs~ or ~hs~~hs~~hs~"""
    def __init__(self):
        super().__init__(
            r'(?:~hs~(?:~hs~)*)',  # Match ~hs~ followed by zero or more ~hs~
            "Horizontal space marker(s)"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> HorizontalSpaceNode:
        # Count how many ~hs~ sequences by dividing total length by 4
        repetitions = len(full_text) // 4
        return HorizontalSpaceNode(
            full_match=full_text,
            inner_content='',
            repetitions=repetitions
        )


class HorizontalSpaceAltPattern(Pattern):
    """Pattern for alternative horizontal space like ~hshs~"""
    def __init__(self):
        super().__init__(
            r'~(?:hs){2,}~',  # Match 2 or more 'hs' between single tildes
            "Alternative horizontal space like ~hshs~"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> HorizontalSpaceAltNode:
        # Count number of 'hs' pairs
        content = full_text[1:-1]  # Remove tildes
        repetitions = len(content) // 2  # Each 'hs' is 2 chars
        return HorizontalSpaceAltNode(
            full_match=full_text,
            inner_content='',
            repetitions=repetitions
        )


class TikiCommentPattern(Pattern):
    """Pattern for Tiki comments like ~tc~comment~/tc~"""
    def __init__(self):
        super().__init__(
            r'(?s)~tc~(.*?)~/tc~',  # Match content between ~tc~ and ~/tc~, including newlines
            "Tiki comment like ~tc~comment~/tc~"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> TikiCommentNode:
        return TikiCommentNode(
            full_match=full_text,
            inner_content=captures[0],
            children=[]
        )


class FontPattern(Pattern):
    """Pattern for FONT tags like {FONT(size="16")}text{FONT}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{FONT\((.*?)\)\}(.*?)\{/?FONT\}',  # Note the /? for optional slash
            "FONT tag like {FONT(size=\"16\")}text{FONT}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> FontNode:
        return FontNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class NewlinePattern(Pattern):
    """Pattern for newline marker %%%"""
    def __init__(self):
        super().__init__(
            r'%%%',
            "Newline marker %%%"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> NewlineNode:
        return NewlineNode(
            full_match=full_text,
            inner_content=''
        )


class FadePattern(Pattern):
    """Pattern for FADE tags like {FADE(label="Click here")}hidden content{FADE}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{FADE\((.*?)\)\}(.*?)\{/?FADE\}',  # Note the /? for optional slash
            "FADE tag like {FADE(label=\"Click here\")}content{FADE}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> FadeNode:
        return FadeNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class ItalixPattern(Pattern):
    """Pattern for italix text like ^italix text^"""
    def __init__(self):
        super().__init__(
            r'\^(.*?)\^',  # Need to escape ^ since it's special in regex
            "Italix text like ^italix text^"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ItalixNode:
        return ItalixNode(
            full_match=full_text,
            inner_content=captures[0],
            children=[]
        )


class ListPagesPattern(Pattern):
    """Pattern for LISTPAGES tags like {LISTPAGES(categId=28)}content{LISTPAGES}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{LISTPAGES\((.*?)\)\}(.*?)\{/?LISTPAGES\}',  # Note the /? for optional slash
            "LISTPAGES tag like {LISTPAGES(categId=28, max=20)}content{LISTPAGES}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ListPagesNode:
        return ListPagesNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class CategoryPattern(Pattern):
    """Pattern for category tags like {category id="XX+YY" types="wiki"}"""
    def __init__(self):
        super().__init__(
            r'\{category\s+(.*?)\}',  # Match attrs after category keyword
            "Category tag like {category id=\"XX+YY\" types=\"wiki\"}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> CategoryNode:
        return CategoryNode(
            full_match=full_text,
            inner_content="",  # No inner content for self-closing tag
            attrs_dict = parse_attrs(captures[0])
        )


class FilterPattern(Pattern):
    """Pattern for filter tags like {filter field="title" content="search terms"}"""
    def __init__(self):
        super().__init__(
            r'\{filter\s+(.*?)\}',  # Match attrs after filter keyword
            "Filter tag like {filter field=\"title\" content=\"search terms\"}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> FilterNode:
        return FilterNode(
            full_match=full_text,
            inner_content="",  # No inner content for self-closing tag
            attrs_dict = parse_attrs(captures[0])
        )


class BoxPattern(Pattern):
    """Pattern for BOX tags like {BOX(title="Title" class="border")} content {BOX}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{BOX\s*\((.*?)\)\}(.*?)\{BOX\}',  # Added (?s) flag to make dot match newlines
            "BOX tag like {BOX(title=\"Title\" class=\"border\")} content {BOX}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> BoxNode:
        return BoxNode(
            full_match=full_text,
            inner_content=captures[1],  # Content between opening and closing tags
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class NoParsePattern(Pattern):
    """Pattern for NoParse tags like ~np~data~/np~"""
    def __init__(self):
        super().__init__(
            r'~np~(.*?)~/np~',  # Match content between ~np~ and ~/np~
            "NoParse tag like ~np~data~/np~"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> NoParseNode:
        return NoParseNode(
            full_match=full_text,
            inner_content=captures[0],
            children=[]
        )


class HtmlPattern(Pattern):
    """Pattern for HTML tags like {HTML()}code{HTML}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{HTML\((.*?)\)\}(.*?)\{/?HTML\}',  # Note the /? for optional slash
            "HTML tag like {HTML()}code{HTML}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> HtmlNode:
        return HtmlNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class AlinkPattern(Pattern):
    """Pattern for ALINK tags like {ALINK(aname=1week)}link text{ALINK}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{ALINK\((.*?)\)\}(.*?)\{/?ALINK\}',  # Note the /? for optional slash
            "ALINK tag like {ALINK(aname=1week)}link text{ALINK}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> AlinkNode:
        return AlinkNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


class ColorPattern(Pattern):
    """Pattern for color tags like ~~attrs:text~~"""
    def __init__(self):
        # TODO:
        #  must handle format like this too:
        #  ~~#06F:foo~~
        super().__init__(
            r'~~([^:]+?):(.*?)~~',  # Capture everything before colon, then content
            "Color tag like ~~white,black:text~~"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ColorNode:
        return ColorNode(
            full_match=full_text,
            inner_content=captures[1],  # Content after the colon
            attrs_dict=parse_attrs(captures[0]),
            children=[]  # Will be populated in parse_generic
        )


class IndentPattern(Pattern):
    """Pattern for indentation like + or ++ or +++ at start of line"""
    def __init__(self):
        super().__init__(
            r'(?m)^(\+{1,})(.*?)(?=\n|$)',  # Match one or more + at START of line, followed by content until end of line
            "Indent like + or ++ or +++ at start of line"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> IndentNode:
        return IndentNode(
            full_match=full_text,
            inner_content=captures[1],  # Content after the +s
            level=len(captures[0]),  # Number of + characters
            children=[]
        )


class RedirectPattern(Pattern):
    """Pattern for redirect tags like {REDIRECT(url=tiki-index.php?page_id=xxxx) /}"""
    def __init__(self):
        super().__init__(
            r'\{REDIRECT\((.*?)\)\s*/\}',  # Match REDIRECT with attrs and self-closing
            "Redirect tag like {REDIRECT(url=...) /}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> RedirectNode:
        return RedirectNode(
            full_match=full_text,
            inner_content="",  # No inner content
            attrs_dict=parse_attrs(captures[0])
        )


class WeirdCitationPattern(Pattern):
    """Pattern for weird citation tags like [[123]"""
    def __init__(self):
        super().__init__(
            r'(\s?)(?<!\[)\[\[([\d\s\*,]+)\](?!\])',  # Match optional space, then [[digits/*/,] but not [[[
            "Weird citation like [[123] or [[63* 64]"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> WeirdCitationNode:
        had_space = len(captures[0]) > 0  # Check if there was a space captured
        return WeirdCitationNode(
            full_match=full_text,
            inner_content=captures[1],  # Just the citation numbers/characters
            citation=captures[1].strip(),  # Clean up any internal spaces
            had_space=had_space
        )


class DoiLinkPattern(Pattern):
    """Pattern for DOI references like "doi: 10.1007/s11912-023-01476-4" """
    def __init__(self):
        super().__init__(
            r'doi:\s+([0-9a-zA-Z./\-_()\[\]]+)',  # Updated to include (), [], and _ characters
            "DOI reference like 'doi: 10.1007/s11912-023-01476-4' or 'doi: 10.1016/0005-2736(84)90033-6'"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> DoiLinkNode:
        if not captures or not captures[0]:
            raise ValueError(f"Invalid DOI reference: '{full_text}'. DOI identifier missing.")
            
        return DoiLinkNode(
            full_match=full_text,
            inner_content=captures[0],
            doi=captures[0]
        )


class HorizontalRulePattern(Pattern):
    """Pattern for horizontal rules like --- in tiki format.
    Aggressively matches horizontal rules even if newlines are part of other nodes."""
    def __init__(self):
        super().__init__(
            r'\n[ \t]*---[ \t]*(?:\n|$)',  # Match --- with optional whitespace and newlines
            "Horizontal rule"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> HorizontalRuleNode:
        return HorizontalRuleNode(
            full_match=full_text,
            inner_content='---'
        )


class HorizontalRuleAltPattern(Pattern):
    """Pattern for horizontal rules like ---- in tiki format.
    Aggressively matches horizontal rules even if newlines are part of other nodes."""

    def __init__(self):
        super().__init__(
            r'\n[ \t]*----[ \t]*(?:\n|$)',  # Match --- with optional whitespace and newlines
            "Horizontal rule alt"
        )

    def create_node(self, full_text: str, captures: List[str]) -> HorizontalRuleAltNode:
        return HorizontalRuleAltNode(
            full_match=full_text,
            inner_content='----'
        )


class ImgBlockPattern(Pattern):
    """Pattern for IMG block tags like {IMG(attId="22584" max="400")}{IMG}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{IMG\(([^}]*)\)\}(.*?)\{/?IMG\}',  # (?s) to allow matching across lines, /? for optional slash
            "IMG block tag like {IMG(attId=\"22584\" max=\"400\")}{IMG}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> ImgBlockNode:
        # Use ImgBlockNode instead of ImgNode for block form
        return ImgBlockNode(
            full_match=full_text,
            inner_content=captures[1],  # This is typically empty for IMG blocks
            attrs_dict=parse_attrs(captures[0])
        )


class SimpleUrlPattern(Pattern):
    """Pattern for simple links like [url]"""
    def __init__(self):
        super().__init__(
            r'\[([^\|\]]+?)\]',  # Match [anything-except-|or]-brackets], non-greedy
            "Simple link like [url]"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> LinkNode:
        url = captures[0]
        return LinkNode(
            full_match=full_text,
            inner_content=url,  # Use URL as the text
            url=url,  # Same URL for both
            children=[]  # Will be populated in parse_link_node
        )


class SqlPattern(Pattern):
    """Pattern for SQL tags like {SQL(db=>vitamind)}query{SQL}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{SQL\((.*?)\)}(.*?)\{/?SQL\}',  # Note the /? for optional slash
            "SQL tag like {SQL(db=>vitamind)}query{SQL}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> SqlNode:
        return SqlNode(
            full_match=full_text,
            inner_content=captures[1],  # The SQL query itself
            attrs_dict=parse_attrs(captures[0])
        )


class CustomSearchPattern(Pattern):
    """Pattern for CUSTOMSEARCH blocks like {CUSTOMSEARCH(wiki="template")}...{CUSTOMSEARCH}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{CUSTOMSEARCH\((.*?)\)\}(.*?)\{/?CUSTOMSEARCH\}',  # (?s) to allow matching across lines, /? for optional slash
            "CUSTOMSEARCH block like {CUSTOMSEARCH(wiki=\"template\")}...{CUSTOMSEARCH}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> CustomSearchNode:
        return CustomSearchNode(
            full_match=full_text,
            inner_content=captures[1],  # The content inside the CUSTOMSEARCH block
            attrs_dict=parse_attrs(captures[0]),
            children=[]  # Will be populated by parsing the inner content if needed
        )


class SupPattern(Pattern):
    """Pattern for superscript text like {SUP()}text{SUP}"""
    def __init__(self):
        super().__init__(
            r'(?s)\{SUP\((.*?)\)\}(.*?)\{SUP\}',  # Match {SUP()}content{SUP} including across lines
            "Superscript text like {SUP()}1,{SUP} or {SUP()}5{SUP}"
        )
    
    def create_node(self, full_text: str, captures: List[str]) -> SupNode:
        if len(captures) < 2:
            raise ValueError(f"Invalid SUP tag format: {full_text}. Expected {{SUP()}}content{{SUP}}")
            
        return SupNode(
            full_match=full_text,
            inner_content=captures[1],
            attrs_dict=parse_attrs(captures[0]),
            children=[]
        )


PATTERNS = [
    CustomSearchPattern(),  # Add this before SqlPattern to ensure proper precedence
    SqlPattern(),
    RedirectPattern(),
    MakeTocPattern(),
    TikiCommentPattern(),
    ListPagesPattern(),
    CategoryPattern(),
    FilterPattern(),
    DoiLinkPattern(),  # Add the DOI pattern before other specific patterns
    ImgBlockPattern(),  # Add the block pattern BEFORE the inline pattern
    ImgPattern(),
    IncludePattern(),
    AliasedLocalLinkPattern(),  # Add this BEFORE LocalLinkPattern (more specific pattern first)
    LocalLinkPattern(),
    AttachPattern(),
    ListPattern(),  # Add ListPattern for {LIST()} blocks
    TablePattern(),  # Add TablePattern for table markup
    ListItemPattern(),
    NumListItemPattern(),
    BoldPattern(),
    LinkPattern(),
    EmphasisPattern(),
    HeadingPattern(),
    HorizontalSpacePattern(),
    HorizontalSpaceAltPattern(),
    FontPattern(),
    FadePattern(),
    ItalixPattern(),
    SupPattern(),  # Add SupPattern before Box and Div patterns since it's more specific
    BoxPattern(),
    DivPattern(),  # Add DivPattern to parse DIV tags
    NoParsePattern(),
    HtmlPattern(),
    AlinkPattern(),
    ColorPattern(),
    IndentPattern(),
    WeirdCitationPattern(),
    HorizontalRulePattern(),
    HorizontalRuleAltPattern(),
    NewlinePattern(),  # Add NewlinePattern for explicit newline handling
    SimpleUrlPattern()
]


def parse_generic(node: Node) -> None:
    if hasattr(node, 'flag_no_parse'):
        if hasattr(node, 'children'):
            node.children = [
                TextNode(
                    full_match=node.inner_content,
                    inner_content=node.inner_content
                )
            ]
        return

    # Handle table parsing
    if isinstance(node, TableNode):
        # Split on either || or newline to get rows
        rows = re.split(r'\|\||(?:\n(?!\|))', node.inner_content)
        node.children = []
        for row_content in rows:
            if not row_content.strip():  # Skip empty rows
                continue
                
            # Protect pipe characters inside link syntax before splitting cells
            # Look for [something|something] patterns and replace | with placeholder
            PIPE_PLACEHOLDER = "%%PIPE_CHAR%%"
            
            def protect_pipes_in_links(match):
                # Replace pipe chars inside link brackets with placeholder
                return match.group(0).replace('|', PIPE_PLACEHOLDER)
            
            # Use regex to find and protect pipes in link patterns
            protected_row = re.sub(r'\[[^\]]*\|[^\]]*\]', protect_pipes_in_links, row_content)
            
            row_node = TableRowNode(
                full_match=row_content,
                inner_content=row_content,
                children=[]
            )
            
            # Split on | to get cells (now with protected pipes in links)
            cells = protected_row.split('|')
            
            for cell_content in cells:
                # Restore original pipe chars for processing within cell
                restored_content = cell_content.replace(PIPE_PLACEHOLDER, '|')
                
                cell_node = TableCellNode(
                    full_match=restored_content,
                    inner_content=restored_content,
                    children=[]
                )
                # Parse cell content for inline formatting (now with proper links)
                cell_node.children = parse(restored_content)
                row_node.children.append(cell_node)
            
            node.children.append(row_node)
        return

    # all other Node types
    if hasattr(node, 'children'):
        node.children = parse(node.inner_content)
        if not node.children:
            node.children = [
                TextNode(
                    full_match=node.inner_content,
                    inner_content=node.inner_content
                )
            ]


def parse(text: str) -> List[Node]:
    """Parse text into a list of nodes"""
    text = text.replace('\r\n', '\n').replace('\r', '\n')  # Normalize line endings
    
    # Remove leading whitespace from each line if configured
    if config.REMOVE_PADDING:
        # Split by lines, remove leading whitespace, then rejoin
        lines = text.split('\n')
        lines = [line.lstrip() for line in lines]
        text = '\n'.join(lines)
        # print(f"DEBUG: Removed leading whitespace from {len(lines)} lines")
        
    nodes = []
    remaining = text
    pos = 0
    text_start = 0
    
    while pos < len(text):
        # Try each pattern
        matched = False
        for pattern in PATTERNS:
            result = pattern.try_match(text, pos)
            if result:

                node, new_pos = result
                
                # Flush any accumulated text
                if pos > text_start:
                    text_node = TextNode(
                        full_match=text[text_start:pos],
                        inner_content=text[text_start:pos]
                    )
                    nodes.append(text_node)
                
                # Parse the inner content for any node type
                parse_generic(node)

                nodes.append(node)
                pos = new_pos
                text_start = pos
                matched = True
                break  # Exit pattern loop since we found a match
        
        # If no pattern matched, move to the next character
        if not matched:
            pos += 1
    
    # Add any remaining text after the last node
    if pos > text_start:
        text_node = TextNode(
            full_match=text[text_start:pos],
            inner_content=text[text_start:pos]
        )
        nodes.append(text_node)
    
    return nodes


def render_as_markdown(nodes: List[Node]) -> str:
    if not isinstance(nodes, list):
        raise TypeError(f"Expected list of nodes, got {type(nodes)}")

    rendered = []
    for i, node in enumerate(nodes):
        if not isinstance(node, BaseNode):
            raise TypeError(f"Node {i} must be BaseNode, got {type(node)}")
        r = node.render()
        rendered.append(r)

    if config.LOOSE_RENDERING:
        # This will lead to "loose lists"
        result = "\n".join(rendered)  # Add newlines between nodes
    else:
        result = "".join(rendered)

    while "\n\n\n" in result:
        result = result.replace("\n\n\n", "\n\n")
    return result


def format_node(node: Node, indent: int = 0) -> str:
    """Format a node and its children as a string with pretty printing"""
    lines = []
    prefix = "│   " * indent
    
    # Format node type
    lines.append(f"{prefix}├── {node.__class__.__name__}")
    
    # Format content with visible whitespace
    full_match_str = node.full_match.replace('\n', '\\n').replace('\t', '\\t')
    inner_content_str = node.inner_content.replace('\n', '\\n').replace('\t', '\\t')

    lines.append(f"{prefix}│   full_match: `{full_match_str}`")
    lines.append(f"{prefix}│   inner_content: `{inner_content_str}`")

    # Format attributes
    if hasattr(node, 'attrs_dict'):
        lines.append(f"{prefix}│   attrs_dict:")
        for k, v in node.attrs_dict.items():
            lines.append(f"{prefix}│   │   {k}: {v}")
    if hasattr(node, 'url'):
        lines.append(f"{prefix}│   url: `{node.url}`")
    if hasattr(node, 'level'):
        lines.append(f"{prefix}│   level: `{node.level}`")
    if hasattr(node, 'depth'):
        lines.append(f"{prefix}│   depth: `{node.depth}`")
    if hasattr(node, 'page'):
        lines.append(f"{prefix}│   page: `{node.page}`")
    if hasattr(node, 'repetitions'):
        lines.append(f"{prefix}│   repetitions: `{node.repetitions}`")
    if hasattr(node, 'citation'):
        lines.append(f"{prefix}│   citation: `{node.citation}`")
    if hasattr(node, 'had_space'):
        lines.append(f"{prefix}│   had_space: `{node.had_space}`")

    # Format children
    if hasattr(node, 'children') and len(node.children) > 0:
        lines.append(f"{prefix}│   children:")
        for child in node.children:
            # Get child's formatted string
            child_lines = format_node(child, indent + 1).split('\n')
            # Add each line of the child's output
            lines.extend(line for line in child_lines if line)
    
    # Join all lines with newlines
    return '\n'.join(lines)


def format_ast(nodes: List[Node]) -> str:
    """Format a list of nodes as a pretty-printed string"""
    result = []
    for node in nodes:
        # Get node's formatted string
        node_lines = format_node(node, 0).split('\n')
        # Add each line, ensuring proper separation
        result.extend(line for line in node_lines if line)
        # Add blank line between top-level nodes
        result.append('')
    
    # Join with newlines and strip any extra whitespace
    return '\n'.join(result).strip()


def _parse_numeric_id(raw_value: str) -> int:
    """Extract and validate a numeric ID from a raw attribute value.

    This function strips surrounding typographic quotes (e.g., “ ”) and
    regular quotes, removes any whitespace, and then validates that the
    remaining characters form a valid integer. If validation fails, it
    raises ValueError with detailed context.
    """
    if raw_value is None:
        raise ValueError("ID value is None; expected numeric string")

    cleaned = raw_value.strip().strip('"\'“”')  # remove common quote chars
    if not cleaned:
        raise ValueError(f"ID value '{raw_value}' is empty after stripping quotes")

    if not cleaned.isdigit():
        raise ValueError(
            f"ID value '{raw_value}' contains non-digit characters after cleaning -> '{cleaned}'"
        )
    return int(cleaned)


def main():
    # run test cases
    tests = []
    if os.path.exists('parsing/tests'):
        dir = 'parsing/tests'
    elif os.path.exists('tests'):
        dir = 'tests'
    else:
        raise Exception('no test dir found')
    for f in sorted(os.listdir(dir)):
        with open(os.path.join(dir, f), 'r') as f:
            txt = f.read()
            tests.append(txt)

    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}:")
        print("=" * 40)
        print(f"Input: `{test}`")
        print("-" * 40)
        nodes = parse(test)
        ast_str = format_ast(nodes)
        print(ast_str)
        print("-" * 40)
        rendered = render_as_markdown(nodes)
        print(f"Rendered output:`\n{rendered}\n`")


if __name__ == "__main__":

    main()