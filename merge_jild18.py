#!/usr/bin/env python3
"""Merge Jild 18 tashreeh chunks into jild-18.json.

Re-runnable: reads every jild-18-chunk-*.json listed in the manifest,
merges in chunk order, validates (unique ids, page coverage, no empty
jawab), writes jild-18.json, and updates the manifest statuses.

INPUT (verified on disk by the coordinator):
  13 chunk files, 149 chunk items, volume_id 46.
  Source export ~/workspace/fatawa-app/content/jild-18.json: 647 DB
  rows, 644 unique pages pp. 5-736. Gaps (88, nothing invented):
  pp. 8-92 (85), 138, 254, 501.

COMBINE RULES (11 cases; parts ordered by min page; sawal from the
FIRST part unless noted; jawab = all parts concatenated in page
order; pages = UNION of all parts' pages; notes = all parts' notes):
  masala 42-43:  chunk 02 'jild18-masala-42-43' [183-188] + chunk 03
              'jild18-masala-42-43' [189-194] -> [183-194]. Ends p. 194,
              NOT p. 190 (verified from source: p. 190 ends only the
              furqat/iddat part; the second sub-question's answer
              continues through pp. 191-193; "مسئلہ ۴۴" first appears
              p. 194).
  masala 59:   chunk 03 [237-238] + chunk 04 [239-241] -> [237-241].
  masala 76:   chunk 04 [289] + chunk 05 [290] -> [289, 290].
  masala 83:   chunk 05 [318-339] + chunk 06 [340-357] -> [318-357].
  masala 90 (THREE-way cross-id): chunk 06 'jild18-masala-90' [389]
              (sawal = سوال اول, jawab EMPTY) + chunk 07
              'jild18-ansah-sawal-1' [390-391] (sawal empty, jawab =
              سوال اول's answer tail) + chunk 07
              'jild18-ansah-sawal-2' [391-404] (sawal = سوال دوم,
              jawab = its answer) -> ONE item 'jild18-masala-90',
              pages [389-404]. Sawal = chunk 06's sawal + chunk 07
              sawal-2's sawal CONCATENATED (Jild 12 masala-289
              precedent — both halves carry different parts of the
              question). Jawab = sawal-1's jawab + sawal-2's jawab
              concatenated (chunk 06's jawab is empty). Net -2 items.
  masala 94 (THIRTEEN-way): chunk 07 'jild18-masala-94' [414-439] +
              ALL 12 of chunk 08's page-based items jild18-p440 ...
              jild18-p463 [440-465] -> ONE item 'jild18-masala-94',
              pages [414-465]. Sawal from chunk 07 (the 12 items have
              empty sawal); jawab = chunk 07's jawab + all 12 items'
              jawabs concatenated in page order. Net -12 items.
              Verified from source: no "مسئلہ" heading on any page
              440-464 (only heading is masala-95 on p. 465); p. 440
              continues p. 439's sentence mid-stream; numbered points
              run continuously 1-8 -> 9-42; span closes with
              "واللہ سبحانہ وتعالیٰ اعلم" on p. 465.
  masala 112:  chunk 08 [487-489] + chunk 09 [490-500] -> [487-500].
  masala 114:  chunk 09 [509-539] + chunk 10 [540-564] -> [509-564].
  masala 126:  chunk 10 [589] + chunk 11 [590] -> [589, 590].
  masala 141:  chunk 11 [624-639] + chunk 12 [640-657] -> [624-657].
  masala 142:  chunk 12 [657-689] + chunk 13 [690-708] -> [657-708].
After all 11 combines: 149 - 23 = 126 items covering 644 unique pages.

RENAMES: none needed. The two Jild 4-precedent renames are already in
the chunk files — jild18-p359 (second printed مسئلہ ۸۶, p. 359; plain
id stays with chunk 05's p. 308 masala-86) and jild18-masala-18-19
(second printed 18, p. 126; plain jild18-masala-18 stays with the
earliest). Do NOT globally normalise bare ids to masala-form. Any
duplicate id left after the combines is a bug: fail loudly, do NOT
silently rename.

DO-NOT-COMBINES: masala-66 [255-276] is one item already, do not
split; khatima [736] standalone; masala-85 does not exist.

SHARED PAGES (legitimate, kept): p. 657 in both masala-141 and
masala-142; pp. 509-510 in both masala-113 and masala-114 (two DB
rows each, one per lesson — lessons' content kept strictly
separate). p. 270 has two DB fragments (same lesson) — covered once,
page listed once.

EMPTY FIELDS: the ONLY empty jawab among all 149 chunk items is
chunk 06's jild18-masala-90 — a split half whose answer lives in
chunk 07's items (combine rule 5 resolves it). The merged file must
have ZERO empty jawab. After merging, the only empty sawals are
pesh-lafz, masala-66 and khatima (by design; their notes explain).
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

# result id -> list of selectors, in page order.
# Selector forms:
#   ('id', sid)            — every item with this id (1 or 2 halves)
#   ('id_start', sid, sp)  — the item with this id starting at page sp
COMBINES = {
    'jild18-masala-42-43': [
        ('id', 'jild18-masala-42-43'),
    ],
    'jild18-masala-59': [
        ('id', 'jild18-masala-59'),
    ],
    'jild18-masala-76': [
        ('id', 'jild18-masala-76'),
    ],
    'jild18-masala-83': [
        ('id', 'jild18-masala-83'),
    ],
    'jild18-masala-90': [
        ('id', 'jild18-masala-90'),
        ('id', 'jild18-ansah-sawal-1'),
        ('id', 'jild18-ansah-sawal-2'),
    ],
    'jild18-masala-94': [
        ('id', 'jild18-masala-94'),
        ('id', 'jild18-p440'),
        ('id', 'jild18-p442'),
        ('id', 'jild18-p444'),
        ('id', 'jild18-p446'),
        ('id', 'jild18-p447'),
        ('id', 'jild18-p450'),
        ('id', 'jild18-p452'),
        ('id', 'jild18-p454'),
        ('id', 'jild18-p456'),
        ('id', 'jild18-p459'),
        ('id', 'jild18-p461'),
        ('id', 'jild18-p463'),
    ],
    'jild18-masala-112': [
        ('id', 'jild18-masala-112'),
    ],
    'jild18-masala-114': [
        ('id', 'jild18-masala-114'),
    ],
    'jild18-masala-126': [
        ('id', 'jild18-masala-126'),
    ],
    'jild18-masala-141': [
        ('id', 'jild18-masala-141'),
    ],
    'jild18-masala-142': [
        ('id', 'jild18-masala-142'),
    ],
}

# masala-90 only: sawal = parts[0] + parts[2] concatenated (both halves
# carry different parts of the question). All other combines take the
# sawal from the first part only.
SAWAL_CONCAT = {
    'jild18-masala-90': [0, 2],
}

# Expected pages for every combined item (spot-check anchors).
EXPECTED_COMBINED_PAGES = {
    'jild18-masala-42-43': list(range(183, 195)),
    'jild18-masala-59': list(range(237, 242)),
    'jild18-masala-76': [289, 290],
    'jild18-masala-83': list(range(318, 358)),
    'jild18-masala-90': list(range(389, 405)),
    'jild18-masala-94': list(range(414, 466)),
    'jild18-masala-112': list(range(487, 501)),
    'jild18-masala-114': list(range(509, 565)),
    'jild18-masala-126': [589, 590],
    'jild18-masala-141': list(range(624, 658)),
    'jild18-masala-142': list(range(657, 709)),
}

# The only ids that may be absorbed by a combine (must be gone after).
ABSORBED = ['jild18-ansah-sawal-1', 'jild18-ansah-sawal-2',
            'jild18-p440', 'jild18-p442', 'jild18-p444', 'jild18-p446',
            'jild18-p447', 'jild18-p450', 'jild18-p452', 'jild18-p454',
            'jild18-p456', 'jild18-p459', 'jild18-p461', 'jild18-p463']

# The only items allowed to keep an empty sawal after merging.
EMPTY_SAWAL_ALLOWED = {'jild18-pesh-lafz', 'jild18-masala-66',
                       'jild18-khatima'}


def combine_parts(result_id, parts):
    parts = sorted(parts, key=lambda it: min(it['pages']))
    first = parts[0]
    if result_id in SAWAL_CONCAT:
        sawal = ''.join((parts[i].get('tashreeh_sawal', '') or '')
                        for i in SAWAL_CONCAT[result_id])
    else:
        sawal = first.get('tashreeh_sawal', '') or ''
    combined = {
        'id': result_id,
        'title': first.get('title') or '',
        'volume_id': 46,
        'pages': sorted(set().union(*[set(p['pages']) for p in parts])),
        'start_page': min(min(p['pages']) for p in parts),
        'tashreeh_sawal': sawal,
        'tashreeh_jawab': ''.join((p.get('tashreeh_jawab', '') or '') for p in parts),
        'notes': [n for p in parts for n in (p.get('notes') or [])],
    }
    return combined


def select_parts(all_items, selectors):
    """Resolve selectors to the matching items (each used at most once)."""
    parts = []
    used = set()
    for sel in selectors:
        if sel[0] == 'id':
            hits = [it for it in all_items
                    if it['id'] == sel[1] and id(it) not in used]
        elif sel[0] == 'id_start':
            hits = [it for it in all_items
                    if it['id'] == sel[1] and it['start_page'] == sel[2]
                    and id(it) not in used]
        else:
            raise ValueError(f'unknown selector {sel}')
        assert hits, f'no items matched selector {sel}'
        for it in hits:
            used.add(id(it))
        parts.extend(hits)
    return parts


def run_merge(manifest_path, base, write=False):
    manifest = json.load(open(manifest_path, encoding='utf-8'))
    all_items = []
    merged_chunks = []
    for entry in manifest['chunks']:
        nn = entry['chunk']
        if entry.get('status') == 'split-halves':
            print(f'chunk {nn}: split-halves placeholder — halves are separate entries, skipping')
            continue
        path = os.path.join(base, entry['file'])
        if not os.path.exists(path):
            print(f'chunk {nn}: not yet written')
            continue
        try:
            d = json.load(open(path, encoding='utf-8'))
        except json.JSONDecodeError as e:
            # File may still be streaming from its translator; skip it
            # for now instead of crashing the whole merge.
            print(f'chunk {nn}: not valid JSON yet ({e}) — skipping for now')
            continue
        items = d['masail']
        # Normalize: some translators omit start_page; derive it from pages.
        for it in items:
            if 'start_page' not in it:
                assert it.get('pages'), f'chunk {nn} item {it.get("id")} has no pages'
                it['start_page'] = it['pages'][0]
                print(f'chunk {nn}: derived start_page={it["start_page"]} for {it["id"]}')
            assert it['start_page'] == min(it['pages']), \
                f'chunk {nn} item {it["id"]}: start_page != first page'
            it['_src_file'] = entry['file']
        all_items.extend(items)
        merged_chunks.append(nn)
        entry['status'] = 'merged'
        print(f'chunk {nn}: {len(items)} items merged')
    print(f'items before combines: {len(all_items)}')
    assert len(all_items) == 149, f'expected 149 chunk items, got {len(all_items)}'
    # COMBINE the 11 cases (one mas'ala split across chunks).
    for result_id, selectors in COMBINES.items():
        parts = select_parts(all_items, selectors)
        combined = combine_parts(result_id, parts)
        assert combined['pages'] == EXPECTED_COMBINED_PAGES[result_id], \
            f'{result_id}: pages {combined["pages"]} != expected {EXPECTED_COMBINED_PAGES[result_id]}'
        assert combined['tashreeh_jawab'], f'{result_id}: combined jawab is empty!'
        assert combined['tashreeh_sawal'], f'{result_id}: combined sawal is empty!'
        assert combined['start_page'] == min(combined['pages']), f'{result_id}: start_page != min(pages)'
        used_ids = set(id(p) for p in parts)
        all_items = [it for it in all_items if id(it) not in used_ids]
        all_items.append(combined)
        print(f'COMBINED {result_id}: {len(parts)} parts, pages {combined["pages"][0]}-{combined["pages"][-1]} '
              f'({len(combined["pages"])} pages), sawal {len(combined["tashreeh_sawal"])} chars, '
              f'jawab {len(combined["tashreeh_jawab"])} chars, notes {len(combined["notes"])}')
    ids = [it['id'] for it in all_items]
    assert len(ids) == len(set(ids)), f'STILL DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}'
    empty = [it['id'] for it in all_items if not it.get('tashreeh_jawab')]
    assert not empty, f'EMPTY JAWAB: {empty}'
    empty_sawal = [it['id'] for it in all_items if not it.get('tashreeh_sawal')]
    assert set(empty_sawal) == EMPTY_SAWAL_ALLOWED, \
        f'EMPTY SAWAL mismatch: {sorted(empty_sawal)} != {sorted(EMPTY_SAWAL_ALLOWED)}'
    print(f'empty sawal (by design only): {sorted(empty_sawal)}')
    pages = set()
    for it in all_items:
        pages.update(it['pages'])
    # PRIMARY coverage check (Jild 17 lesson): validate against the 644
    # unique pages directly, not against a range-minus-gaps computation.
    assert len(pages) == 644, f'expected 644 unique pages, got {len(pages)}'
    assert min(pages) == 5 and max(pages) == 736, \
        f'page span {min(pages)}-{max(pages)} != 5-736'
    # Secondary cross-check: manifest ranges minus listed gap pages.
    expected = set()
    for entry in manifest['chunks']:
        if entry['chunk'] in merged_chunks:
            expected.update(range(entry['start_page'], entry['end_page'] + 1))
            expected.difference_update(entry['missing_pages'])
    missing_covered = expected - pages
    extra = pages - expected
    print(f'total items: {len(all_items)} | pages covered: {len(pages)} | expected (manifest): {len(expected)}')
    print(f'uncovered expected pages: {sorted(missing_covered)}')
    print(f'extra pages (outside merged chunks): {sorted(extra)}')
    assert not missing_covered, 'pages missing from merged chunks!'
    assert not extra, 'pages outside merged chunks!'
    assert len(all_items) == 126, f'expected 126 items after combines, got {len(all_items)}'
    # sort by start_page for the final file
    all_items.sort(key=lambda it: it['start_page'])
    for it in all_items:
        it.pop('_src_file', None)
    if write:
        with open(os.path.join(base, 'jild-18.json'), 'w', encoding='utf-8') as f:
            json.dump({'masail': all_items}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(base, 'chunks-manifest-jild18.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f'WROTE jild-18.json: {len(all_items)} items, {len(pages)} pages, chunks merged: {merged_chunks}')
    return all_items, pages, merged_chunks


def main():
    manifest_path = os.path.join(BASE, 'chunks-manifest-jild18.json')
    run_merge(manifest_path, BASE, write=True)


if __name__ == '__main__':
    main()
