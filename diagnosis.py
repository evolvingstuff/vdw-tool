#!/usr/bin/env python3
import json
import os
import re
import sys
from collections import Counter, defaultdict

import config


def load_json(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required data file: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_object_mappings(objects):
    name_to_obj_ids = defaultdict(list)
    item_to_obj_ids = defaultdict(list)
    object_id_to_name = {}
    object_id_to_item = {}

    for entry in objects:
        if entry.get('type') != 'wiki page':
            continue
        try:
            obj_id = int(entry['objectId'])
        except Exception as e:
            raise ValueError(f"Invalid objectId in tiki_objects: {entry}") from e
        name = entry.get('name') or ''
        item = entry.get('itemId') or ''

        object_id_to_name[obj_id] = name
        object_id_to_item[obj_id] = item
        name_to_obj_ids[name].append(obj_id)
        item_to_obj_ids[item].append(obj_id)

    # Deterministic single mapping (first occurrence) for resolution trials
    name_to_obj = {k: v[0] for k, v in name_to_obj_ids.items() if v}
    item_to_obj = {k: v[0] for k, v in item_to_obj_ids.items() if v}

    return {
        'name_to_obj_ids': name_to_obj_ids,
        'item_to_obj_ids': item_to_obj_ids,
        'name_to_obj': name_to_obj,
        'item_to_obj': item_to_obj,
        'object_id_to_name': object_id_to_name,
        'object_id_to_item': object_id_to_item,
    }


def build_category_mappings(category_objects, categories):
    obj_to_cat_ids = defaultdict(list)
    for row in category_objects:
        try:
            obj_id = int(row['catObjectId'])
            cat_id = int(row['categId'])
        except Exception as e:
            raise ValueError(f"Invalid row in category objects: {row}") from e
        obj_to_cat_ids[obj_id].append(cat_id)

    cat_id_to_name = {}
    for row in categories:
        try:
            cat_id = int(row['categId'])
        except Exception as e:
            raise ValueError(f"Invalid categId in categories: {row}") from e
        cat_id_to_name[cat_id] = row.get('name', '')

    return obj_to_cat_ids, cat_id_to_name


def categories_for_object(obj_id: int, obj_to_cat_ids, cat_id_to_name):
    cat_ids = obj_to_cat_ids.get(obj_id, [])
    names = []
    missing_name_ids = []
    for cid in cat_ids:
        nm = cat_id_to_name.get(cid)
        if nm is None:
            missing_name_ids.append(cid)
        else:
            names.append(nm)
    return names, cat_ids, missing_name_ids


def analyze():
    print("=== VDW Diagnosis Report ===")
    print("Using config paths:")
    print(f"  PATH_TIKI_PAGES:          {config.PATH_TIKI_PAGES}")
    print(f"  PATH_TIKI_OBJECTS:        {config.PATH_TIKI_OBJECTS}")
    print(f"  PATH_CATEGORY_OBJECTS:    {config.PATH_CATEGORY_OBJECTS}")
    print(f"  PATH_TIKI_CATEGORIES:     {config.PATH_TIKI_CATEGORIES}")
    print()

    pages = load_json(config.PATH_TIKI_PAGES)
    objects = load_json(config.PATH_TIKI_OBJECTS)
    category_objects = load_json(config.PATH_CATEGORY_OBJECTS)
    categories = load_json(config.PATH_TIKI_CATEGORIES)

    # Duplicates in pages
    page_names = [p.get('pageName') for p in pages]
    page_name_counts = Counter(page_names)
    page_name_dup_count = sum(1 for c in page_name_counts.values() if c > 1)
    print(f"Pages total: {len(pages)}")
    print(f"Distinct page names: {len(page_name_counts)}  (duplicates: {page_name_dup_count})")
    if page_name_dup_count:
        sample_dups = [name for name, cnt in page_name_counts.items() if cnt > 1][:10]
        print(f"  Sample duplicate titles: {sample_dups}")
    print()

    # Object mappings
    maps = build_object_mappings(objects)
    name_to_obj_ids = maps['name_to_obj_ids']
    item_to_obj_ids = maps['item_to_obj_ids']
    name_to_obj = maps['name_to_obj']
    item_to_obj = maps['item_to_obj']

    name_key_dups = sum(1 for v in name_to_obj_ids.values() if len(v) > 1)
    item_key_dups = sum(1 for v in item_to_obj_ids.values() if len(v) > 1)
    print("Object mapping collisions:")
    print(f"  name→objectId: {name_key_dups} keys map to multiple objectIds")
    print(f"  itemId→objectId: {item_key_dups} keys map to multiple objectIds")
    if name_key_dups or item_key_dups:
        print("  Note: collisions imply potential category assignment ambiguity for duplicates.")
    print()

    # Category mappings
    obj_to_cat_ids, cat_id_to_name = build_category_mappings(category_objects, categories)
    print(f"Category objects: {len(category_objects)} associations")
    print(f"Categories: {len(cat_id_to_name)} named entries")
    print()

    # Per-page resolution using name vs itemId mapping
    resolved_by_name = resolved_by_item = 0
    both_resolved = only_name_resolved = only_item_resolved = neither_resolved = 0
    zero_cats_by_name = zero_cats_by_item = both_zero = 0
    differences_count = 0
    sample_differences = []

    reason_counts_name = Counter()
    reason_counts_item = Counter()

    for p in pages:
        page_name = p.get('pageName')

        obj_n = name_to_obj.get(page_name)
        obj_i = item_to_obj.get(page_name)

        resolved_n = obj_n is not None
        resolved_i = obj_i is not None

        if resolved_n:
            resolved_by_name += 1
        if resolved_i:
            resolved_by_item += 1
        if resolved_n and resolved_i:
            both_resolved += 1
        elif resolved_n:
            only_name_resolved += 1
        elif resolved_i:
            only_item_resolved += 1
        else:
            neither_resolved += 1

        cats_n = []
        miss_cat_n = []
        if resolved_n:
            names_n, ids_n, missing_n = categories_for_object(obj_n, obj_to_cat_ids, cat_id_to_name)
            cats_n = names_n
            miss_cat_n = missing_n

        cats_i = []
        miss_cat_i = []
        if resolved_i:
            names_i, ids_i, missing_i = categories_for_object(obj_i, obj_to_cat_ids, cat_id_to_name)
            cats_i = names_i
            miss_cat_i = missing_i

        if len(cats_n) == 0:
            zero_cats_by_name += 1
            if not resolved_n:
                reason_counts_name['no_object'] += 1
            else:
                if obj_n not in obj_to_cat_ids or len(obj_to_cat_ids[obj_n]) == 0:
                    reason_counts_name['no_cat_objects'] += 1
                elif len(miss_cat_n) == len(obj_to_cat_ids[obj_n]):
                    reason_counts_name['cat_id_missing_name'] += 1
                else:
                    reason_counts_name['other'] += 1

        if len(cats_i) == 0:
            zero_cats_by_item += 1
            if not resolved_i:
                reason_counts_item['no_object'] += 1
            else:
                if obj_i not in obj_to_cat_ids or len(obj_to_cat_ids[obj_i]) == 0:
                    reason_counts_item['no_cat_objects'] += 1
                elif len(miss_cat_i) == len(obj_to_cat_ids[obj_i]):
                    reason_counts_item['cat_id_missing_name'] += 1
                else:
                    reason_counts_item['other'] += 1

        if len(cats_n) == 0 and len(cats_i) == 0:
            both_zero += 1

        if set(cats_n) != set(cats_i):
            differences_count += 1
            if len(sample_differences) < 20:
                sample_differences.append({
                    'pageName': page_name,
                    'name_obj': obj_n,
                    'item_obj': obj_i,
                    'cats_name': cats_n,
                    'cats_item': cats_i,
                })

    print("Page→objectId resolution (by title key):")
    print(f"  Resolved by name:   {resolved_by_name}")
    print(f"  Resolved by itemId: {resolved_by_item}")
    print(f"  Both resolved:      {both_resolved}")
    print(f"  Only name:          {only_name_resolved}")
    print(f"  Only itemId:        {only_item_resolved}")
    print(f"  Neither:            {neither_resolved}")
    print()

    print("Pages with zero categories (by resolution path):")
    print(f"  Zero via name:      {zero_cats_by_name}")
    print(f"  Zero via itemId:    {zero_cats_by_item}")
    print(f"  Zero via both:      {both_zero}")
    print()

    print("Zero-category reasons (name path):")
    for k in ('no_object', 'no_cat_objects', 'cat_id_missing_name', 'other'):
        print(f"  {k}: {reason_counts_name.get(k, 0)}")
    print("Zero-category reasons (itemId path):")
    for k in ('no_object', 'no_cat_objects', 'cat_id_missing_name', 'other'):
        print(f"  {k}: {reason_counts_item.get(k, 0)}")
    print()

    print(f"Category set differences between name vs itemId mapping: {differences_count}")
    if differences_count:
        print("  Sample differences (up to 20):")
        for d in sample_differences:
            print(f"    - {d['pageName']}: name_obj={d['name_obj']} item_obj={d['item_obj']}\n"
                  f"      cats(name)={d['cats_name']}\n"
                  f"      cats(item)={d['cats_item']}")
    print()

    # Link debug summary (optional)
    link_debug_stats = {}
    if os.path.exists('link_debug.log'):
        exists_false = 0
        exists_true = 0
        total = 0
        with open('link_debug.log', 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                total += 1
                if 'exists=False' in line:
                    exists_false += 1
                elif 'exists=True' in line:
                    exists_true += 1
        link_debug_stats = {
            'lines': total,
            'exists_true': exists_true,
            'exists_false': exists_false,
        }
        print("Link debug summary:")
        print(f"  lines={total} exists_true={exists_true} exists_false={exists_false}")
        print()

    # Errors log summary (optional)
    failed_pages = []
    if os.path.exists('errors.log'):
        with open('errors.log', 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                m = re.search(r"\[\d+\]\:\\t?(.+)$", line.strip())
                if m:
                    failed_pages.append(m.group(1).strip())
        print("Errors log summary:")
        try:
            with open('errors.log', 'r', encoding='utf-8', errors='ignore') as f:
                header = f.readline().strip()
            print(f"  {header}")
        except Exception:
            pass
        if failed_pages:
            print(f"  Sample failed pages (up to 10): {failed_pages[:10]}")
        print()

    print("=== End of Report ===")


if __name__ == '__main__':
    try:
        analyze()
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        sys.exit(1)

