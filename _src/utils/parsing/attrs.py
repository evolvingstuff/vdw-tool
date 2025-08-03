from typing import Dict
import re


def parse_attrs(attrs: str) -> Dict[str, str]:
    """Parse attribute string into key-value pairs.
    
    Handles formats:
    - key="value"
    - key=""  (empty values)
    - (key=value)
    - (key="value")
    - key=value
    - Multiple space-separated attributes
    - Empty attributes (returns just raw_content)
    
    Args:
        attrs: Raw attribute string, can be empty
        
    Returns:
        Dict of parsed attributes, always includes raw_content
    """
    result = {'raw_content': attrs if attrs is not None else ''}
    
    # If attrs is None or empty, just return raw_content
    if not attrs:
        return result
        
    if not isinstance(attrs, str):
        return result
    
    # Remove outer parentheses if present
    cleaned = attrs.strip()
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = cleaned[1:-1].strip()
    
    # If still empty after cleaning, return just raw_content
    if not cleaned:
        return result
    
    # First split on unquoted commas
    parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', cleaned)
    
    # For each comma-separated part, also split on spaces between complete attr=value pairs
    for part in parts:
        # Use regex to find all attribute patterns, handling both quoted and unquoted values
        matches = re.finditer(r'([^=\s]+)\s*=\s*(?:"([^"]*)"|([^\s"]*))', part)
        
        for match in matches:
            key = match.group(1).strip()
            # Group 2 is quoted value, Group 3 is unquoted value
            # Use empty string if both are None (handles empty quotes)
            value = (match.group(2) if match.group(2) is not None 
                    else match.group(3) if match.group(3) is not None 
                    else "")
            
            if key:  # Only add if we have a valid key
                result[key] = value
            
    return result


if __name__ == '__main__':
    tests = [
        '''page="60 percent more life births after infertility diagnosis if Vitamin D fortification (Denmark) - Nov 2019" start="~tc~ start ~/tc~" stop="~tc~ end ~/tc~"''',
        '(class=x)',
        ' type="attId" attId="21139" width="400"',
        '(class="lefth4")',
        ' Title=""',
        '(inline="1" id="22000" icon="1")',
        'size="16"',
        'label="CLICK HERE to see the scientific proof for each health problem treated by bi-weekly 50,000 IU" icon="y" bootstrap="n" class="pagetitle" categId = 28, max = 20, sort = "lastModif_desc"',
        ' id="XX+YY" types="wiki" sort="created_desc" split="n" and="y" sub="n" showdescription="n" showname="y" showtype="n" one="y" showTitle="n"',
    ]
    for i, test in enumerate(tests, 1):
        print(f"\nTest {i}:")
        print(test)
        result = parse_attrs(test)
        print('ATTRIBUTES:')
        for k, v in result.items():
            print(f"\t{k}: {v}")
