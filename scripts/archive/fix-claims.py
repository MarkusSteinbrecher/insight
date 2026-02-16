#!/usr/bin/env python3
"""
Fix claim-alignment.yaml:
  1. Re-align all seg-tbd entries to actual segment IDs from raw files
  2. Add source-055 comment-only references to actual supporting_sources

Usage:
    python3 scripts/fix-claims.py <topic-slug>
"""

import sys
import re
import yaml
from pathlib import Path
from collections import defaultdict

# ── Source-055 cross-references (from comment block in YAML) ─────

SOURCE_055_REFS = {
    'cc-069': ['seg-004', 'seg-006', 'seg-007'],
    'cc-070': ['seg-011', 'seg-029', 'seg-030'],
    'cc-077': ['seg-078', 'seg-079', 'seg-080'],
    'cc-082': ['seg-012', 'seg-016'],
    'cc-071': ['seg-049'],
    'cc-093': ['seg-049', 'seg-050', 'seg-066'],
    'cc-010': ['seg-050'],
    'cc-017': ['seg-071', 'seg-072', 'seg-073'],
    'cc-061': ['seg-054', 'seg-055', 'seg-056', 'seg-057'],
    'cc-074': ['seg-058', 'seg-059', 'seg-060'],
    'cc-043': ['seg-058', 'seg-059'],
    'cc-045': ['seg-051', 'seg-052', 'seg-060'],
    'cc-113': ['seg-069'],
    'cc-013': ['seg-085'],
    'cc-084': ['seg-077'],
}

STOPWORDS = {
    'the', 'and', 'for', 'that', 'with', 'from', 'this', 'are',
    'not', 'but', 'have', 'has', 'can', 'will', 'its', 'into',
    'than', 'also', 'more', 'how', 'their', 'they', 'which',
    'been', 'being', 'about', 'over', 'such', 'only', 'other',
    'through', 'where', 'most', 'should', 'would', 'could',
    'does', 'did', 'each', 'between', 'those', 'while', 'these',
    'what', 'when', 'who', 'all', 'any', 'both', 'few', 'many',
    'some', 'then', 'very', 'just', 'because', 'before', 'after',
}


# ── Helpers ──────────────────────────────────────────────────────

def load_raw_segments(raw_dir):
    """Load all raw segment files into {source_id: {seg_id: {text, type}}}."""
    all_segments = {}
    for path in sorted(raw_dir.glob('source-*-raw.yaml')):
        source_id = path.stem.replace('-raw', '')
        with open(path) as f:
            data = yaml.safe_load(f)
        segments = {}
        for seg in data.get('segments', []):
            segments[seg['id']] = {
                'text': seg.get('text', ''),
                'type': seg.get('type', ''),
            }
        all_segments[source_id] = segments
    return all_segments


def content_words(text):
    """Extract content words from text."""
    return set(re.findall(r'[a-z]{3,}', text.lower())) - STOPWORDS


def find_best_segment(note, claim_stmt, segments):
    """
    Find the segment that best matches the note text.
    Returns (seg_id, seg_text, score).
    """
    if not segments:
        return None, '', 0

    note_words = content_words(note or '')
    claim_words = content_words(claim_stmt or '')
    # Combine: note words are primary, claim words are secondary
    search_words = note_words | claim_words

    if not search_words:
        return None, '', 0

    best_id = None
    best_text = ''
    best_score = -1

    for seg_id, seg_data in segments.items():
        seg_text = seg_data['text']
        seg_type = seg_data['type']
        seg_words = content_words(seg_text)

        # Primary: note word overlap
        note_overlap = len(note_words & seg_words) if note_words else 0
        # Secondary: claim statement overlap
        claim_overlap = len(claim_words & seg_words) if claim_words else 0
        # Type bonus: prefer substantive segments
        type_bonus = 0.3 if seg_type in ('claim', 'recommendation',
                                          'evidence', 'statistic') else 0

        # Combined score: note overlap weighted 2x
        score = note_overlap * 2 + claim_overlap + type_bonus

        if score > best_score:
            best_score = score
            best_id = seg_id
            best_text = seg_text

    return best_id, best_text, best_score


def yaml_escape(text):
    """Escape text for a YAML double-quoted string."""
    return text.replace('\\', '\\\\').replace('"', '\\"')


# ── Scan the file for seg-tbd entries ────────────────────────────

def scan_tbd_entries(lines):
    """
    Find all seg-tbd entries and their context.
    Returns list of dicts with line numbers, source_id, claim_id, note, etc.
    """
    entries = []
    for i, line in enumerate(lines):
        if 'seg_id: seg-tbd' not in line:
            continue

        indent = len(line) - len(line.lstrip())

        # Find source_id (look back up to 5 lines)
        source_id = None
        source_line = None
        for j in range(i - 1, max(0, i - 6), -1):
            m = re.search(r'source_id:\s*(source-\d+)', lines[j])
            if m:
                source_id = m.group(1)
                source_line = j
                break

        # Find note (look forward 1 line)
        note = None
        note_line = None
        if i + 1 < len(lines):
            m = re.search(r'note:\s*"(.+?)"', lines[i + 1])
            if not m:
                m = re.search(r"note:\s*'(.+?)'", lines[i + 1])
            if not m:
                m = re.search(r'note:\s*(.+?)\s*$', lines[i + 1])
            if m:
                note = m.group(1)
                note_line = i + 1

        # Find claim_id (look back up to 150 lines)
        claim_id = None
        for j in range(i - 1, max(0, i - 150), -1):
            m = re.search(r'^\s+-?\s*id:\s*(cc-\d+|uc-\d+|ct-\d+)',
                          lines[j])
            if m:
                claim_id = m.group(1)
                break

        # Find claim statement (look for statement: after the id line)
        claim_stmt = None
        if claim_id:
            for j in range(i - 1, max(0, i - 150), -1):
                m = re.search(r'id:\s*' + re.escape(claim_id), lines[j])
                if m:
                    # Look forward from id line for statement
                    for k in range(j + 1, min(len(lines), j + 5)):
                        sm = re.search(r'statement:\s*"(.+?)"', lines[k])
                        if sm:
                            claim_stmt = sm.group(1)
                            break
                    break

        # Determine section type
        section = 'canonical'
        if claim_id and claim_id.startswith('uc-'):
            section = 'unique'
        elif claim_id and claim_id.startswith('ct-'):
            section = 'contradiction'

        entries.append({
            'tbd_line': i,
            'source_id': source_id,
            'source_line': source_line,
            'claim_id': claim_id,
            'claim_stmt': claim_stmt,
            'note': note,
            'note_line': note_line,
            'indent': indent,
            'section': section,
        })

    return entries


# ── Find insertion points for source-055 ─────────────────────────

def find_insertion_points(lines, claim_ids):
    """
    For each claim_id, find the line where new supporting_sources entries
    should be inserted (just before source_count or strength or next claim).
    Returns {claim_id: insert_after_line}.
    """
    points = {}

    for claim_id in claim_ids:
        # Find the line with this claim's id
        id_line = None
        for i, line in enumerate(lines):
            if re.search(r'id:\s*' + re.escape(claim_id) + r'\s*$', line):
                id_line = i
                break

        if id_line is None:
            print(f'  WARNING: Could not find claim {claim_id} for insertion')
            continue

        # From the id line, find the end of supporting_sources
        # Look for source_count:, strength:, claim_type:, or next claim
        insert_after = None
        in_sources = False
        last_source_line = None

        for j in range(id_line + 1, min(len(lines), id_line + 200)):
            line = lines[j].rstrip()

            if 'supporting_sources:' in line:
                in_sources = True
                continue

            if in_sources:
                # Track the last line of the last source entry
                stripped = line.strip()
                if stripped.startswith('- source_id:'):
                    last_source_line = j
                elif stripped.startswith('seg_id:') or \
                     stripped.startswith('quote:') or \
                     stripped.startswith('note:'):
                    last_source_line = j
                elif stripped.startswith('source_count:') or \
                     stripped.startswith('strength:') or \
                     stripped.startswith('claim_type:') or \
                     stripped.startswith('- id:') or \
                     (stripped == '' and last_source_line is not None):
                    # End of supporting_sources
                    insert_after = last_source_line
                    break

        if insert_after is not None:
            points[claim_id] = insert_after
        else:
            print(f'  WARNING: Could not find insertion point for {claim_id}')

    return points


# ── Build edit operations ─────────────────────────────────────────

def build_edits(entries, raw_segments, lines):
    """
    Build a list of edit operations from the scanned entries.
    Each edit: {'type': 'replace', 'start': N, 'end': N, 'new_lines': [...]}
    """
    edits = []
    match_log = []

    for entry in entries:
        source_id = entry['source_id']
        claim_id = entry['claim_id']
        note = entry['note']
        claim_stmt = entry['claim_stmt']
        tbd_line = entry['tbd_line']
        note_line = entry['note_line']
        indent = entry['indent']
        section = entry['section']

        # Find best matching segment
        segments = raw_segments.get(source_id, {})
        best_seg, best_text, score = find_best_segment(
            note, claim_stmt, segments
        )

        if best_seg is None:
            match_log.append(
                f'  SKIP {claim_id} / {source_id}: no segments found'
            )
            continue

        match_log.append(
            f'  {claim_id:>8} / {source_id}: {best_seg} '
            f'(score={score:.1f}) "{best_text[:60]}..."'
        )

        indent_str = ' ' * indent

        if section in ('canonical', 'contradiction'):
            # Replace seg_id line and note line
            new_seg_line = f'{indent_str}seg_id: {best_seg}\n'
            escaped_text = yaml_escape(best_text)
            new_quote_line = f'{indent_str}quote: "{escaped_text}"\n'

            if note_line is not None:
                # Replace 2 lines: seg_id + note → seg_id + quote
                edits.append({
                    'type': 'replace',
                    'start': tbd_line,
                    'end': note_line,
                    'new_lines': [new_seg_line, new_quote_line],
                })
            else:
                # Replace just the seg_id line, add quote
                edits.append({
                    'type': 'replace',
                    'start': tbd_line,
                    'end': tbd_line,
                    'new_lines': [new_seg_line, new_quote_line],
                })

        elif section == 'unique':
            # Just replace the seg_id line
            new_seg_line = f'{indent_str}seg_id: {best_seg}\n'
            edits.append({
                'type': 'replace',
                'start': tbd_line,
                'end': tbd_line,
                'new_lines': [new_seg_line],
            })

    return edits, match_log


def build_source_055_edits(insertion_points, raw_segments, lines):
    """Build insertion edits for source-055 references."""
    edits = []
    seg_data = raw_segments.get('source-055', {})
    if not seg_data:
        print('  WARNING: source-055 raw segments not found')
        return edits

    log = []
    for claim_id, seg_ids in SOURCE_055_REFS.items():
        if claim_id not in insertion_points:
            continue

        insert_after = insertion_points[claim_id]

        # Determine indentation from existing entries
        # Look at the line at insert_after to get the indent
        ref_line = lines[insert_after]
        # Find the indent of a source_id line near this position
        source_indent = None
        for j in range(insert_after, max(0, insert_after - 5), -1):
            if '- source_id:' in lines[j]:
                source_indent = len(lines[j]) - len(lines[j].lstrip())
                break
        if source_indent is None:
            source_indent = 6  # default for canonical claims

        indent_str = ' ' * source_indent
        sub_indent = ' ' * (source_indent + 2)

        new_lines = []
        for seg_id in seg_ids:
            seg = seg_data.get(seg_id, {})
            seg_text = seg.get('text', '')

            new_lines.append(
                f'{indent_str}- source_id: source-055\n'
            )
            new_lines.append(
                f'{sub_indent}seg_id: {seg_id}\n'
            )
            if seg_text:
                escaped = yaml_escape(seg_text)
                new_lines.append(
                    f'{sub_indent}quote: "{escaped}"\n'
                )

        if new_lines:
            edits.append({
                'type': 'insert',
                'after': insert_after,
                'new_lines': new_lines,
            })
            log.append(
                f'  {claim_id}: +{len(seg_ids)} entries '
                f'({", ".join(seg_ids)})'
            )

    return edits, log


# ── Apply edits ──────────────────────────────────────────────────

def apply_edits(lines, edits):
    """Apply all edits bottom-to-top to preserve line numbers."""
    # Sort by position, descending
    def sort_key(edit):
        if edit['type'] == 'insert':
            return edit['after']
        return edit['start']

    sorted_edits = sorted(edits, key=sort_key, reverse=True)

    result = list(lines)
    for edit in sorted_edits:
        if edit['type'] == 'replace':
            start = edit['start']
            end = edit['end']
            result[start:end + 1] = edit['new_lines']
        elif edit['type'] == 'insert':
            after = edit['after']
            for i, new_line in enumerate(edit['new_lines']):
                result.insert(after + 1 + i, new_line)

    return result


# ── Remove source-055 comment block ─────────────────────────────

def remove_comment_block(lines):
    """Remove the SOURCE-055 INTEGRATION comment block."""
    start = None
    end = None

    for i, line in enumerate(lines):
        if 'SOURCE-055 INTEGRATION' in line:
            # Find the start of this comment block (look back for separator)
            start = i
            for j in range(i - 1, max(0, i - 5), -1):
                if lines[j].strip().startswith('# ===='):
                    start = j
                    break
            # Find the end (last comment line before data or blank+data)
            for j in range(i + 1, min(len(lines), i + 30)):
                stripped = lines[j].strip()
                if not stripped.startswith('#') and stripped != '':
                    end = j - 1
                    # Also remove trailing blank lines
                    while end >= start and lines[end].strip() == '':
                        end -= 1
                    break
            break

    if start is not None and end is not None:
        # Remove the block
        del lines[start:end + 1]
        return True
    return False


# ── Update source_count fields ───────────────────────────────────

def update_source_counts(lines, claim_data, added_claims):
    """
    Update source_count fields for claims that got new source-055 entries.
    """
    for claim_id in added_claims:
        # Find the claim in the lines
        for i, line in enumerate(lines):
            if re.search(r'id:\s*' + re.escape(claim_id) + r'\s*$', line):
                # Find the source_count line
                for j in range(i + 1, min(len(lines), i + 200)):
                    m = re.match(r'(\s*)source_count:\s*(\d+)', lines[j])
                    if m:
                        old_count = int(m.group(2))
                        # Count source-055 segments being added
                        new_sources = len(SOURCE_055_REFS.get(claim_id, []))
                        # source_count counts distinct sources, not entries
                        # Adding source-055 adds 1 new source
                        new_count = old_count + 1
                        lines[j] = f'{m.group(1)}source_count: {new_count}\n'
                        break
                    # Stop if we hit the next claim
                    if re.search(r'^\s+-?\s*id:\s*(cc-|uc-|ct-)', lines[j]):
                        break
                break


# ── Main ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 scripts/fix-claims.py <topic-slug>')
        sys.exit(1)

    topic = sys.argv[1]
    base = Path('knowledge-base/topics') / topic
    ca_path = base / 'extractions' / 'claim-alignment.yaml'
    raw_dir = base / 'raw'

    if not ca_path.exists():
        print(f'Error: {ca_path} not found')
        sys.exit(1)

    # ── Load data ──
    print('Loading data...')
    raw_segments = load_raw_segments(raw_dir)
    print(f'  Loaded {len(raw_segments)} raw segment files')

    with open(ca_path) as f:
        lines = f.readlines()
    print(f'  Claim-alignment: {len(lines)} lines')

    # ── Step 1: Scan for seg-tbd entries ──
    print('\nScanning for seg-tbd entries...')
    tbd_entries = scan_tbd_entries(lines)
    print(f'  Found {len(tbd_entries)} seg-tbd entries')

    # ── Step 2: Build replacement edits ──
    print('\nMatching segments...')
    replace_edits, match_log = build_edits(tbd_entries, raw_segments, lines)
    for msg in match_log:
        print(msg)
    print(f'\n  Built {len(replace_edits)} replacement edits')

    # ── Step 3: Find insertion points for source-055 ──
    print('\nFinding insertion points for source-055...')
    insertion_points = find_insertion_points(lines, SOURCE_055_REFS.keys())
    print(f'  Found {len(insertion_points)} insertion points')

    # ── Step 4: Build source-055 insertion edits ──
    print('\nBuilding source-055 entries...')
    insert_edits, insert_log = build_source_055_edits(
        insertion_points, raw_segments, lines
    )
    for msg in insert_log:
        print(msg)
    print(f'\n  Built {len(insert_edits)} insertion edits')

    # ── Step 5: Apply all edits ──
    all_edits = replace_edits + insert_edits
    print(f'\nApplying {len(all_edits)} total edits...')
    new_lines = apply_edits(lines, all_edits)

    # ── Step 6: Remove source-055 comment block ──
    if remove_comment_block(new_lines):
        print('  Removed SOURCE-055 INTEGRATION comment block')

    # ── Step 7: Update source_count fields ──
    update_source_counts(new_lines, None, list(SOURCE_055_REFS.keys()))
    print('  Updated source_count fields')

    # ── Step 8: Write ──
    with open(ca_path, 'w') as f:
        f.writelines(new_lines)
    print(f'\nWritten {len(new_lines)} lines to {ca_path}')

    # ── Summary ──
    print('\n' + '=' * 60)
    print('  SUMMARY')
    print('=' * 60)
    print(f'  seg-tbd entries fixed:      {len(replace_edits)}')
    print(f'  source-055 claims added:    {len(insert_edits)}')
    total_055_segs = sum(len(v) for v in SOURCE_055_REFS.values())
    print(f'  source-055 entries added:   {total_055_segs}')
    print(f'  Comment block removed:      yes')
    print(f'  source_count fields updated: {len(SOURCE_055_REFS)}')
    print()
    print('  Run audit to verify: python3 scripts/audit-claims.py '
          f'"{topic}"')


if __name__ == '__main__':
    main()
