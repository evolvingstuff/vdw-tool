
import sys
import os
sys.path.append('_src/actions')

from sync_posts_from_s3 import sync_posts
from build_hugo import build_hugo_site
from serve_hugo import serve_hugo_site
from convert_tiki_data import convert_tiki_data
from deploy_hugo_site import deploy_hugo_site

def show_menu():
    print('\n' + '='*50)
    print('VDW Tool - Build Pipeline')
    print('='*50)
    print('1) Convert TikiWiki Data to Markdown')
    print('2) Sync Posts from S3')
    print('3) Build Hugo Site')
    print('4) Serve Hugo Site (localhost:1313)')
    print('5) Deploy Hugo Site to S3/CloudFront')
    print('6) Exit')
    print('='*50)

def main():
    show_menu()

    while True:
        response = input('>> ')
        if response == '1':
            convert_tiki_data()
            show_menu()
        elif response == '2':
            sync_posts()
            show_menu()
        elif response == '3':
            build_hugo_site()
            show_menu()
        elif response == '4':
            serve_hugo_site()
            show_menu()
        elif response == '5':
            deploy_hugo_site()
            show_menu()
        elif response == '6':
            print('Goodbye')
            break
        else:
            print('Invalid option')
            show_menu()


if __name__ == '__main__':
    main()
