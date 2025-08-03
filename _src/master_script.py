
import sys
import os
sys.path.append('_src/actions')

from sync_posts_from_s3 import sync_posts
from build_hugo import build_hugo_site
from serve_hugo import serve_hugo_site

def main():
    print('Master Script')
    print('')
    print('Options:')
    print('1) Hello World')
    print('2) Sync Posts from S3')
    print('3) Build Hugo Site')
    print('4) Serve Hugo Site (localhost:1313)')
    print('5) Exit')

    while True:
        response = input('>> ')
        if response == '1':
            print('Hello World')
        elif response == '2':
            sync_posts()
        elif response == '3':
            build_hugo_site()
        elif response == '4':
            serve_hugo_site()
        elif response == '5':
            print('Goodbye')
            break
        else:
            print('Invalid option')


if __name__ == '__main__':
    main()
