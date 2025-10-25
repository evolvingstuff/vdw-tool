import json
import tempfile
import zipfile
import shutil
import os
from utils.filenames import sanitize_filename


root = '../vdw-external-data'
tiki_files = 'tiki_files_2025-10-24.json'
tiki_wiki_attachments = 'tiki_wiki_attachments_2025-10-24.json'
zipped_files = [
    'vitamindwiki_file_gallery-20251018T020347Z-1-001.zip',
    'vitamindwiki_wiki_attachments-20251018T020332Z-1-001.zip',
    'vitamindwiki_wiki_attachments-20251018T020332Z-1-002.zip',
    'vitamindwiki_wiki_attachments-20251018T020332Z-1-003.zip',
    'vitamindwiki_wiki_attachments-20251018T020332Z-1-004.zip'
]
destination = 'named-attachments'
valid_extensions = [
    '_unknown',
    'bmp',
    'csv',
    'doc',
    'docx',
    'epub',
    'flv',
    'gif',
    'html',
    'jfif',
    'jpg',
    'jpeg',
    'mp3',
    'mp4',
    'pdf',
    'png',
    'ppt',
    'pptx',
    'rtf',
    'svg',
    'tif',
    'txt',
    'webp',
    'xls',
    'xlsx',
    'xml',
    'zip'
]


def main():
    print("Converting attachments...")

    for dir in valid_extensions:
        os.makedirs(f'data/attachments/{dir}', exist_ok=True)

    hex_to_filename = {}
    file_id_to_hex = {}
    att_id_to_hex = {}
    errors, success = 0, 0
    invalid_extensions = []
    missing_file_ids = 0
    for path in [tiki_files, tiki_wiki_attachments]:
        with open(f'{root}/{path}', 'r') as f:
            file_data = json.load(f)
            for file in file_data:
                try:
                    assert 'filename' in file, 'missing filename'
                    file_name = file['filename']
                    extension = file_name.split('.')[-1]
                    assert 'path' in file, 'missing path entry'
                    assert file['path'] is not None, 'path entry is None'
                    hex_path = file['path'].split('.')[0]  # sometimes have extensions
                    if extension.lower() not in valid_extensions:
                        invalid_extensions.append(file_name)
                        raise Exception(f'invalid extension: {extension}')
                    hex_path = hex_path + '.' + extension  # TODO: pretty sure we want path here but need to confirm

                    if 'fileId' in file:
                        id = file['fileId']
                        assert id not in file_id_to_hex, 'duplicate file id'
                        file_id_to_hex[id] = hex_path
                        print(f'file:{id} -> {hex_path} -> {file_name}')
                    elif 'attId' in file:
                        id = file['attId']
                        assert id not in att_id_to_hex, 'duplicate att id'
                        att_id_to_hex[id] = hex_path
                        print(f'att: {id} -> {hex_path} -> {file_name}')
                    else:
                        missing_file_ids += 1
                        raise ValueError('missing fileId and attId')

                    assert hex_path not in hex_to_filename, f'{hex_path} -> {file_name} duplicate'
                    hex_to_filename[hex_path] = file_name
                    success += 1
                except KeyError as e:
                    errors += 1
                    print(e)
                except Exception as e:
                    errors += 1
                    print(e)

    print(f"Total json errors: {errors}")
    print(f"Total json success: {success}")
    for invalid_extension in invalid_extensions:
        print(f"\tInvalid extension: {invalid_extension}")
    print(f"missing fileids: {missing_file_ids}")

    # check for existence of hex names

    # Open the zip file
    hit, miss = 0, 0
    for zipped_file in zipped_files:
        path = f'{root}/zips/{zipped_file}'
        with zipfile.ZipFile(path, 'r') as zip_ref:
            # Get the list of file names
            file_names = zip_ref.namelist()

            # Iterate through the file names
            for file_name in file_names:

                # print(f'File name: {file_name}')

                file_name = file_name.split('/')[-1]

                if file_name not in hex_to_filename:
                    # print(f'\tMiss: {file_name}')
                    miss += 1
                else:
                    hit += 1

    print(f"Total missed files: {miss}")
    print(f"Total hit files:    {hit}")

    # extract and rename files
    missing_files = []
    for zipped_file in zipped_files:
        path = f'{root}/zips/{zipped_file}'

        with zipfile.ZipFile(path, 'r') as zip_ref:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract everything to temp directory
                zip_ref.extractall(temp_dir)

                # Process the extracted files
                for extracted_dir in os.listdir(temp_dir):
                    print(extracted_dir)
                    for extracted_file in os.listdir(f'{temp_dir}/{extracted_dir}'):
                        print(f'\t{extracted_file}')
                        file_type = extracted_file.split('.')[-1]
                        if file_type not in valid_extensions:
                            file_type = '_unknown'
                        temp_file_path = f'{temp_dir}/{extracted_dir}/{extracted_file}'
                        if os.path.isfile(temp_file_path):
                            # Your logic here - read, process, rename, whatever
                            print(f"Processing: {extracted_file}")

                            # Rename using your function
                            if extracted_file in hex_to_filename:
                                readable_name = hex_to_filename[extracted_file]
                                readable_file_type = readable_name.split('.')[-1]
                                assert readable_file_type == file_type, 'mismatched file type'
                            else:
                                missing_files.append(extracted_file)
                                print(f'WARNING: {extracted_file} is not in dict')

                            sanitized_readable_name = sanitize_filename(readable_name)

                            # Move to your destination
                            final_path = f'data/attachments/{file_type}/{sanitized_readable_name}'
                            print(f'moving {temp_file_path} to {final_path}')
                            shutil.move(temp_file_path, final_path)
                        else:
                            raise Exception(f'{temp_file_path} is not a file')

    print(f"Total missing files: {len(missing_files)}")
    print(f"Total hit files: {hit}")

    return att_id_to_hex, file_id_to_hex, hex_to_filename


if __name__ == "__main__":
    main()
