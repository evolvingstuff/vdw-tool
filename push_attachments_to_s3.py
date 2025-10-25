import os


def main():
    path_attachments = 'data/attachments/'
    dirs = os.listdir(path_attachments)
    for dir in sorted(dirs):
        if dir == '.DS_Store':
            continue
        dir_path = path_attachments + dir
        print(dir_path)
        for filename in sorted(os.listdir(dir_path)):
            if filename == '.DS_Store':
                continue
            print(f'\t{filename}')
    raise NotImplementedError('TODO...')


if __name__ == '__main__':
    main()
