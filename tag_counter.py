import os

import config
import json

def main():
    print('TAG COUNTER')
    with open(config.PATH_TIKI_CATEGORIES, 'r') as f:
        categories = json.load(f)
    map_cat_id_to_cat_name = {}
    map_cat_name_to_cat_id = {}
    for row in categories:
        cat_id = row['categId']
        cat_name = row['name']
        map_cat_id_to_cat_name[cat_id] = cat_name
        map_cat_name_to_cat_id[cat_name] = cat_id
    with open(config.PATH_CATEGORY_OBJECTS, 'r') as f:
        category_objects = json.load(f)
    map_obj_id_to_cat_ids = {}
    map_cat_id_to_obj_ids = {}
    for row in category_objects:
        obj_id = row['catObjectId']
        cat_id = row['categId']
        if obj_id not in map_obj_id_to_cat_ids:
            map_obj_id_to_cat_ids[obj_id] = []
        map_obj_id_to_cat_ids[obj_id].append(cat_id)
        if cat_id not in map_cat_id_to_obj_ids:
            map_cat_id_to_obj_ids[cat_id] = []
        map_cat_id_to_obj_ids[cat_id].append(obj_id)
    cat_names = sorted(map_cat_id_to_cat_name.values())
    map_obj_id_to_type = {}
    map_obj_id_to_page_name = {}
    with open(config.PATH_TIKI_OBJECTS, 'r') as f:
        objects = json.load(f)
    for row in objects:
        obj_id = row['objectId']
        typ = row['type']
        page_name = row['name']
        map_obj_id_to_type[obj_id] = typ
        map_obj_id_to_page_name[obj_id] = page_name
    tot_page, tot_non_page, tot_missing = 0, 0, 0
    unique_page_names = set()
    for i, cat_name in enumerate(cat_names, 1):
        cat_id = map_cat_name_to_cat_id[cat_name]
        obj_ids = map_cat_id_to_obj_ids[cat_id]
        page, non_page, missing = 0, 0, 0
        unique_pages = set()
        for obj_id in obj_ids:
            if obj_id not in map_obj_id_to_type:
                missing += 1
            elif map_obj_id_to_type[obj_id] == 'wiki page':
                page += 1
                page_name = map_obj_id_to_page_name[obj_id]
                unique_pages.add(page_name)
                unique_page_names.add(page_name)
            else:
                non_page += 1
        tot_page += page
        tot_non_page += non_page
        tot_missing += missing
        print(f'[{i}] {cat_name} -> {len(obj_ids)} ({page} page, {non_page} non-page, {missing} missing)')
    print('')
    print(f'Total page/tags: {tot_page}')
    print(f'Total non-pages: {tot_non_page}')
    print(f'Total missing: {tot_missing}')

    page_names = set()
    with open(config.PATH_TIKI_PAGES, 'r') as f:
        pages = json.load(f)
    dups = 0
    for page in pages:
        page_name = page['pageName']
        if page_name in page_names:
            dups += 1
        page_names.add(page_name)


    print(f'TOTAL PAGES: {len(pages)}, DUPS: {dups}')

    # path = '../vdw-posts/posts'
    # bad_matches = ['tiki-index.php?']
    # tot_bad_matches = 0
    # tot_bad_match_pages = 0
    # for page in sorted(os.listdir(path)):
    #     if not page.endswith('.md'):
    #         continue
    #     matched_page = False
    #     with open(os.path.join(path, page), 'r') as f:
    #         lines = f.readlines()
    #     for line in lines:
    #         line = line.lower()
    #         matched = False
    #         for bad_match in bad_matches:
    #             if bad_match in line:
    #                 matched = True
    #                 matched_page = True
    #                 tot_bad_matches += 1
    #                 break
    #         if matched:
    #             print(line)
    #     if matched_page:
    #         tot_bad_match_pages += 1
    #         print(page)
    #         print('-----------')
    # print(f'TOTAL BAD MATCHES: {tot_bad_matches}')
    # print(f'TOTAL BAD MATCH PAGES: {tot_bad_match_pages}')


if __name__ == '__main__':
    main()
