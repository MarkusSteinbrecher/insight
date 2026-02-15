#!/usr/bin/env python3
"""
Dataset Integrity Audit

Performs three checks on claim-alignment data:
  1. Structural integrity — seg-tbd placeholder detection
  2. AI relevance — keyword density per source
  3. Claim-source coherence — whether seg-tbd notes match source content

Usage:
    python3 scripts/audit-claims.py <topic-slug>
"""

import sys
import os
import re
import yaml
from pathlib import Path
from collections import defaultdict

# ── AI keyword list ──────────────────────────────────────────────

AI_KEYWORDS = [
    r'\bAI\b', r'\bartificial intelligence\b', r'\bagentic\b', r'\bLLM\b',
    r'\bmachine learning\b', r'\bgenerative AI\b', r'\bGenAI\b', r'\bagent\b',
    r'\bagents\b', r'\bmodel\b', r'\bneural\b', r'\bdeep learning\b',
    r'\btransformer\b', r'\bNLP\b', r'\binference\b', r'\bfoundation model\b',
    r'\bcopilot\b', r'\bchatbot\b', r'\bGPT\b', r'\bautonomous\b',
]

AI_PATTERN = re.compile('|'.join(AI_KEYWORDS), re.IGNORECASE)


# ── Helpers ──────────────────────────────────────────────────────

def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_source_number(source_id):
    """source-053 → 53"""
    m = re.search(r'(\d+)', source_id)
    return int(m.group(1)) if m else None


def tokenize(text):
    """Simple word tokenization for coherence check."""
    return set(re.findall(r'[a-z]{3,}', text.lower()))


# ── Build reference index from claim-alignment.yaml ──────────────

def build_reference_index(claim_data):
    """
    Returns {source_id: [{ claim_id, claim_section, seg_id, note_or_quote, claim_statement }]}
    Covers canonical_claims, unique_claims, and contradictions.
    """
    index = defaultdict(list)

    # Canonical claims
    for claim in claim_data.get('canonical_claims', []):
        cid = claim['id']
        stmt = claim.get('statement', '')
        for ref in claim.get('supporting_sources', []):
            index[ref['source_id']].append({
                'claim_id': cid,
                'claim_section': 'canonical',
                'seg_id': ref.get('seg_id', ''),
                'note_or_quote': ref.get('note', ref.get('quote', '')),
                'claim_statement': stmt,
            })

    # Unique claims
    for claim in claim_data.get('unique_claims', []):
        cid = claim['id']
        sid = claim.get('source_id', '')
        index[sid].append({
            'claim_id': cid,
            'claim_section': 'unique',
            'seg_id': claim.get('seg_id', ''),
            'note_or_quote': claim.get('statement', ''),
            'claim_statement': claim.get('statement', ''),
        })

    # Contradictions
    for ct in claim_data.get('contradictions', []):
        cid = ct['id']
        for position_key in ('position_a', 'position_b'):
            pos = ct.get(position_key, {})
            for ref in pos.get('sources', []):
                index[ref['source_id']].append({
                    'claim_id': cid,
                    'claim_section': 'contradiction',
                    'seg_id': ref.get('seg_id', ''),
                    'note_or_quote': pos.get('statement', ''),
                    'claim_statement': ct.get('description', ''),
                })

    return index


# ── Check 1: seg-tbd audit ───────────────────────────────────────

def check_seg_tbd(ref_index, raw_dir):
    """Count seg-tbd per source. Check if raw file exists."""
    results = {}
    for source_id, refs in sorted(ref_index.items()):
        tbd = [r for r in refs if r['seg_id'] == 'seg-tbd']
        proper = [r for r in refs if r['seg_id'] != 'seg-tbd']
        num = extract_source_number(source_id)
        raw_file = raw_dir / f'{source_id}-raw.yaml'
        raw_exists = raw_file.exists()
        results[source_id] = {
            'total_refs': len(refs),
            'tbd_count': len(tbd),
            'proper_count': len(proper),
            'raw_exists': raw_exists,
            'tbd_claims': sorted(set(r['claim_id'] for r in tbd)),
        }
    return results


# ── Check 2: AI relevance ────────────────────────────────────────

def check_ai_relevance(sources_dir):
    """Score each source markdown by AI keyword density."""
    results = {}
    for path in sorted(sources_dir.glob('source-*.md')):
        source_id = path.stem  # source-053
        text = load_text(path)
        matches = AI_PATTERN.findall(text)
        word_count = len(text.split())
        results[source_id] = {
            'ai_keyword_count': len(matches),
            'word_count': word_count,
            'density': round(len(matches) / max(word_count, 1) * 100, 2),
            'title': '',  # filled from frontmatter
        }
        # Extract title from frontmatter
        fm_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
        if fm_match:
            results[source_id]['title'] = fm_match.group(1)
    return results


# ── Check 3: Coherence ───────────────────────────────────────────

def check_coherence(ref_index, raw_dir):
    """
    For seg-tbd entries: check if the note's key terms appear in the
    source's raw segment texts.
    """
    results = []
    raw_cache = {}

    for source_id, refs in sorted(ref_index.items()):
        tbd_refs = [r for r in refs if r['seg_id'] == 'seg-tbd']
        if not tbd_refs:
            continue

        raw_file = raw_dir / f'{source_id}-raw.yaml'
        if not raw_file.exists():
            for r in tbd_refs:
                results.append({
                    'source_id': source_id,
                    'claim_id': r['claim_id'],
                    'note': r['note_or_quote'][:80],
                    'issue': 'no raw file',
                    'overlap_pct': 0,
                })
            continue

        # Load and cache raw segment texts
        if source_id not in raw_cache:
            raw_data = load_yaml(raw_file)
            all_text = ' '.join(
                seg.get('text', '') for seg in raw_data.get('segments', [])
            )
            raw_cache[source_id] = tokenize(all_text)

        source_tokens = raw_cache[source_id]

        for r in tbd_refs:
            note = r['note_or_quote']
            if not note:
                results.append({
                    'source_id': source_id,
                    'claim_id': r['claim_id'],
                    'note': '(empty)',
                    'issue': 'no note provided',
                    'overlap_pct': 0,
                })
                continue

            note_tokens = tokenize(note)
            # Remove very common words
            stopwords = {
                'the', 'and', 'for', 'that', 'with', 'from', 'this', 'are',
                'not', 'but', 'have', 'has', 'can', 'will', 'its', 'into',
                'than', 'also', 'more', 'how', 'their', 'they', 'which',
                'been', 'being', 'about', 'over', 'such', 'only', 'other',
                'through', 'where', 'most', 'should', 'would', 'could',
                'does', 'did', 'each', 'between', 'those', 'while',
            }
            content_tokens = note_tokens - stopwords
            if not content_tokens:
                continue

            overlap = content_tokens & source_tokens
            overlap_pct = round(len(overlap) / len(content_tokens) * 100, 1)

            if overlap_pct < 50:
                results.append({
                    'source_id': source_id,
                    'claim_id': r['claim_id'],
                    'note': note[:80],
                    'issue': 'low term overlap',
                    'overlap_pct': overlap_pct,
                    'missing_terms': sorted(content_tokens - source_tokens)[:8],
                })

    return results


# ── Check 4: Source-055 comment-only references ───────────────────

def check_comment_only_refs(claim_alignment_path, ref_index):
    """
    Detect sources whose cross-references exist only as YAML comments
    (like source-055) rather than in actual supporting_sources entries.
    """
    text = load_text(claim_alignment_path)
    # Find source IDs mentioned in comments
    comment_refs = defaultdict(set)
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#'):
            for m in re.finditer(r'(cc-\d+|uc-\d+|ct-\d+)', stripped):
                claim_id = m.group(1)
                # Look for source ID in nearby context (same comment block)
                src_match = re.search(r'source-(\d+)', stripped)
                if not src_match:
                    # Check the broader comment block context
                    continue

    # Simpler approach: find source IDs that appear in comments referencing
    # canonical claims but don't appear in the actual supporting_sources
    # for those claims
    comment_lines = [l for l in text.split('\n') if l.strip().startswith('#')]
    comment_text = '\n'.join(comment_lines)

    # Find sections like "# Cross-references to existing canonical claims:"
    # followed by "#   cc-NNN (description): seg-XXX, seg-YYY"
    results = []
    cross_ref_pattern = re.compile(
        r'#\s+(cc-\d+)\s+\([^)]+\):\s+((?:seg-\d+(?:,\s*)?)+)',
    )
    for m in cross_ref_pattern.finditer(comment_text):
        claim_id = m.group(1)
        segments = m.group(2).strip().rstrip(',')
        # Find which source section this comment is in
        # Look backwards for SOURCE-NNN header
        pos = m.start()
        preceding = comment_text[:pos]
        source_match = re.search(
            r'SOURCE-(\d+)\s+INTEGRATION',
            preceding,
            re.IGNORECASE,
        )
        # Find the LAST match (closest preceding header)
        all_matches = list(re.finditer(
            r'SOURCE-(\d+)\s+INTEGRATION',
            preceding,
            re.IGNORECASE,
        ))
        if all_matches:
            last_match = all_matches[-1]
            source_id = f'source-{last_match.group(1).zfill(3)}'
            # Check if this source actually appears in the claim's
            # supporting_sources
            actual_refs = ref_index.get(source_id, [])
            actual_claims = {r['claim_id'] for r in actual_refs}
            if claim_id not in actual_claims:
                results.append({
                    'source_id': source_id,
                    'claim_id': claim_id,
                    'segments': segments,
                    'status': 'comment-only (not in supporting_sources)',
                })

    return results


# ── Report printer ───────────────────────────────────────────────

def print_report(tbd_results, relevance_results, coherence_results,
                 comment_only_results, ref_index):
    sep = '=' * 72

    # ── Summary ──
    total_refs = sum(r['total_refs'] for r in tbd_results.values())
    total_tbd = sum(r['tbd_count'] for r in tbd_results.values())
    total_proper = sum(r['proper_count'] for r in tbd_results.values())
    sources_affected = sum(
        1 for r in tbd_results.values() if r['tbd_count'] > 0
    )
    total_sources = len(relevance_results)

    print(sep)
    print('  DATASET INTEGRITY AUDIT')
    print(sep)
    print()
    print(f'  Total source references in claim-alignment:  {total_refs}')
    print(f'  Proper segment IDs:                          {total_proper}')
    print(f'  Placeholder (seg-tbd):                       {total_tbd}')
    print(f'  Sources with placeholders:                   {sources_affected}')
    print(f'  Total sources in sources/:                   {total_sources}')
    print()

    # ── Check 1: seg-tbd table ──
    print(sep)
    print('  CHECK 1: seg-tbd PLACEHOLDERS')
    print(sep)
    print()
    print(f'  {"Source":<14} {"Total":>6} {"Proper":>7} {"seg-tbd":>8} '
          f'{"Raw exists":>11} {"Affected claims"}')
    print(f'  {"─"*14} {"─"*6} {"─"*7} {"─"*8} {"─"*11} {"─"*30}')

    for source_id in sorted(tbd_results.keys(),
                            key=lambda s: extract_source_number(s)):
        r = tbd_results[source_id]
        if r['tbd_count'] == 0 and r['total_refs'] <= 5:
            continue  # Skip clean sources with few refs for brevity
        raw_str = 'yes' if r['raw_exists'] else 'NO'
        claims_str = ', '.join(r['tbd_claims'][:8])
        if len(r['tbd_claims']) > 8:
            claims_str += f' (+{len(r["tbd_claims"]) - 8} more)'
        marker = ' ◀' if r['tbd_count'] > 0 else ''
        print(f'  {source_id:<14} {r["total_refs"]:>6} {r["proper_count"]:>7} '
              f'{r["tbd_count"]:>8} {raw_str:>11} {claims_str}{marker}')

    print()

    # ── Check 2: AI relevance ──
    print(sep)
    print('  CHECK 2: AI RELEVANCE CLASSIFICATION')
    print(sep)
    print()

    # Sort by keyword count ascending to show outliers first
    sorted_rel = sorted(relevance_results.items(),
                        key=lambda x: x[1]['ai_keyword_count'])

    # Determine threshold: flag sources with < 3 AI keywords
    THRESHOLD = 3
    flagged = [(sid, r) for sid, r in sorted_rel
               if r['ai_keyword_count'] < THRESHOLD]
    normal = [(sid, r) for sid, r in sorted_rel
              if r['ai_keyword_count'] >= THRESHOLD]

    if flagged:
        print(f'  FLAGGED — below {THRESHOLD} AI keywords:')
        print()
        print(f'  {"Source":<14} {"AI kw":>6} {"Words":>7} {"Density":>8}  '
              f'{"Title"}')
        print(f'  {"─"*14} {"─"*6} {"─"*7} {"─"*8}  {"─"*40}')
        for sid, r in flagged:
            print(f'  {sid:<14} {r["ai_keyword_count"]:>6} '
                  f'{r["word_count"]:>7} {r["density"]:>7}%  '
                  f'{r["title"][:50]}')
        print()

    print(f'  All sources by AI keyword density (bottom 15):')
    print()
    print(f'  {"Source":<14} {"AI kw":>6} {"Words":>7} {"Density":>8}  '
          f'{"Title"}')
    print(f'  {"─"*14} {"─"*6} {"─"*7} {"─"*8}  {"─"*40}')
    for sid, r in sorted_rel[:15]:
        flag = ' ◀' if r['ai_keyword_count'] < THRESHOLD else ''
        print(f'  {sid:<14} {r["ai_keyword_count"]:>6} '
              f'{r["word_count"]:>7} {r["density"]:>7}%  '
              f'{r["title"][:50]}{flag}')
    print()

    # ── Check 3: Coherence ──
    print(sep)
    print('  CHECK 3: CLAIM-SOURCE COHERENCE')
    print(sep)
    print()

    if coherence_results:
        print(f'  Flagged {len(coherence_results)} references with low '
              f'term overlap:')
        print()
        print(f'  {"Source":<14} {"Claim":<9} {"Overlap":>8}  '
              f'{"Note / Issue"}')
        print(f'  {"─"*14} {"─"*9} {"─"*8}  {"─"*45}')
        for r in coherence_results:
            missing = ''
            if r.get('missing_terms'):
                missing = f'  missing: {", ".join(r["missing_terms"][:5])}'
            print(f'  {r["source_id"]:<14} {r["claim_id"]:<9} '
                  f'{r["overlap_pct"]:>7}%  '
                  f'{r["note"][:45]}{missing}')
    else:
        print('  No coherence issues detected.')
    print()

    # ── Check 4: Comment-only references ──
    if comment_only_results:
        print(sep)
        print('  CHECK 4: COMMENT-ONLY REFERENCES (not in data)')
        print(sep)
        print()
        print(f'  {len(comment_only_results)} cross-references exist only '
              f'as YAML comments:')
        print()
        print(f'  {"Source":<14} {"Claim":<9} {"Segments":<30} {"Status"}')
        print(f'  {"─"*14} {"─"*9} {"─"*30} {"─"*35}')
        for r in comment_only_results:
            print(f'  {r["source_id"]:<14} {r["claim_id"]:<9} '
                  f'{r["segments"]:<30} {r["status"]}')
        print()

    # ── Recommended actions ──
    print(sep)
    print('  RECOMMENDED ACTIONS')
    print(sep)
    print()

    # Sources needing re-alignment (have seg-tbd + raw file exists + AI relevant)
    realign = []
    remove = []
    for source_id, r in tbd_results.items():
        if r['tbd_count'] == 0:
            continue
        rel = relevance_results.get(source_id, {})
        ai_count = rel.get('ai_keyword_count', 0)
        if ai_count < THRESHOLD:
            remove.append((source_id, r['tbd_count'], ai_count))
        elif r['raw_exists']:
            realign.append((source_id, r['tbd_count'], ai_count))
        else:
            remove.append((source_id, r['tbd_count'], ai_count))

    if realign:
        print('  RE-ALIGN (seg-tbd → proper segment IDs):')
        for sid, tbd, ai in sorted(realign):
            print(f'    {sid}: {tbd} placeholder refs, '
                  f'raw file available, {ai} AI keywords')
        print()

    if remove:
        print('  REVIEW/REMOVE (low AI relevance or no raw file):')
        for sid, tbd, ai in sorted(remove):
            print(f'    {sid}: {tbd} placeholder refs, '
                  f'{ai} AI keywords')
        print()

    if comment_only_results:
        sources_in_comments = sorted(set(
            r['source_id'] for r in comment_only_results
        ))
        print('  ADD COMMENT-ONLY REFS TO DATA:')
        for sid in sources_in_comments:
            claims = [r['claim_id'] for r in comment_only_results
                      if r['source_id'] == sid]
            print(f'    {sid}: add to {len(claims)} canonical claims '
                  f'({", ".join(claims[:5])}{"..." if len(claims) > 5 else ""})')
        print()


# ── Main ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 scripts/audit-claims.py <topic-slug>')
        sys.exit(1)

    topic = sys.argv[1]
    base = Path('knowledge-base/topics') / topic

    claim_alignment_path = base / 'extractions' / 'claim-alignment.yaml'
    raw_dir = base / 'raw'
    sources_dir = base / 'sources'

    if not claim_alignment_path.exists():
        print(f'Error: {claim_alignment_path} not found')
        sys.exit(1)

    print(f'Loading claim-alignment from: {claim_alignment_path}')
    claim_data = load_yaml(claim_alignment_path)
    ref_index = build_reference_index(claim_data)
    print(f'Built index: {len(ref_index)} sources, '
          f'{sum(len(v) for v in ref_index.values())} references')
    print()

    # Run checks
    tbd_results = check_seg_tbd(ref_index, raw_dir)
    relevance_results = check_ai_relevance(sources_dir)
    coherence_results = check_coherence(ref_index, raw_dir)
    comment_only_results = check_comment_only_refs(
        claim_alignment_path, ref_index
    )

    # Print report
    print_report(tbd_results, relevance_results, coherence_results,
                 comment_only_results, ref_index)


if __name__ == '__main__':
    main()
