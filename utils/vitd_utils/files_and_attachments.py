import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Add utils to path

import config
from typing import Dict
import utils.vitd_utils.globals
from utils.models import Attachment, TikiFile
from utils.vitd_utils.filenames import sanitize_filename


def map_id_to_path(id_type: str, id: int, attachment_type: str) -> str:
    try:
        # TODO: actually implement this for real once we have the data
        #  also need a separate mapping for files vs attachments
        #  also so point at cloudfront
        path = None

        if id_type == 'fileId':
            assert id in utils.vitd_utils.globals.file_id_to_tiki_file, 'missing file id'
            tiki_file = utils.vitd_utils.globals.file_id_to_tiki_file[id]
            raw_filename = tiki_file.filename
            sanitized_filename = sanitize_filename(raw_filename)
            attachment_type = tiki_file.filename.split('.')[-1]
            path = f'{config.CLOUDFRONT_URL}/attachments/{attachment_type}/{sanitized_filename}'

        elif id_type in ['id', 'attId']:
            try:
                assert id in utils.vitd_utils.globals.att_id_to_file, 'missing att id loc 2'
                att: Attachment = utils.vitd_utils.globals.att_id_to_file[id]
            except AssertionError as e:
                if config.IGNORE_MISSING_APP_ID:
                    path = config.unknown_path
                    return path
                else:
                    raise e
            raw_filename = att.filename
            sanitized_filename = sanitize_filename(raw_filename)
            attachment_type = att.filetype.split('/')[-1]
            path = f'{config.CLOUDFRONT_URL}/attachments/{attachment_type}/{sanitized_filename}'
        else:
            raise ValueError(f'Unexpected id: {id_type}')

        if path is not None:
            return path

        print('about to crash')

        raise ValueError(f'Attachment type {attachment_type} not supported <<<')
    except Exception as e:
        if config.IGNORE_MISSING_APP_ID:
            return config.unknown_path
        else:
            raise ValueError(f'Unexpected id: {id_type}')
