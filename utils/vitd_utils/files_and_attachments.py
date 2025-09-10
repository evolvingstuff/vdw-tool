import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Add utils to path

import config
import utils.vitd_utils.globals
from utils.models import Attachment
from utils.vitd_utils.filenames import sanitize_filename


def map_id_to_path(id_type: str, id: int, attachment_type: str) -> str:
    # TODO: actually implement this for real once we have the data
    #  asdfasdfasdf
    #  also need a separate mapping for files vs attachments
    #  also so point at cloudfront
    path = None

    if id_type == 'fileId':
        # TODO: asdfasdfasdf
        pass
    elif id_type in ['id', 'attId']:
        assert id in utils.vitd_utils.globals.att_id_to_file, 'missing id'
        att: Attachment = utils.vitd_utils.globals.att_id_to_file[id]
        raw_filename = att.filename
        sanitized_file_name = sanitize_filename(raw_filename)
        attachment_type = att.filetype.split('/')[-1]
        path = f'{config.CLOUDFRONT_URL}/attachments/{attachment_type}/{sanitized_file_name}'
    else:
        raise ValueError(f'Unexpected id: {id_type}')

    if path is not None:
        return path

    if attachment_type == 'pdf':
        return '/attachments/d3.mock.pdf'
    elif attachment_type == 'img':
        return '/attachments/d3.mock.jpg'
    else:
        raise ValueError(f'Attachment type {attachment_type} not supported')
