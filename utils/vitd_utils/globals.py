from typing import Dict, Optional
from models import Attachment, TikiFile

# Global variables
att_id_to_file: Optional[Dict[int, Attachment]] = None
file_id_to_tiki_file: Optional[Dict[int, TikiFile]] = None