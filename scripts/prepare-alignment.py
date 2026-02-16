#!/usr/bin/env python3
"""Pre-process raw segmentation files for claim alignment.

Extracts claim-relevant segments (claim, recommendation, statistic, evidence)
from all raw/*.yaml files, clusters them by keyword similarity, and outputs
a condensed YAML file that the LLM can use for cross-source claim alignment.

This reduces the LLM's input from the full raw dataset (e.g., 44K lines / 110K
tokens for 56 sources) to just the relevant segments grouped into candidate
theme clusters (typically 60-70% reduction).

Usage:
    python3 scripts/prepare-alignment.py "EA for AI"
    python3 scripts/prepare-alignment.py "EA for AI" --min-cluster 2
    python3 scripts/prepare-alignment.py "EA for AI" --threshold 0.15

Output:
    extractions/alignment-input.yaml

Requires:
    - pip install pyyaml
"""

import argparse
import glob
import math
import os
import re
import sys
from collections import Counter, defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS_DIR = os.path.join(ROOT, "knowledge-base", "topics")

# Segment types to extract for alignment
RELEVANT_TYPES = {"claim", "recommendation", "statistic", "evidence"}

# Stopwords to exclude from TF-IDF
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "it", "its", "this",
    "that", "these", "those", "as", "if", "not", "no", "than", "more",
    "also", "such", "their", "they", "them", "we", "our", "which", "what",
    "who", "how", "when", "where", "all", "each", "both", "few", "most",
    "other", "some", "any", "only", "very", "so", "up", "out", "about",
    "into", "over", "after", "before", "between", "through", "during",
    "above", "below", "while", "then", "once", "here", "there", "just",
    "well", "still", "even", "much", "many", "new", "used", "using",
    "use", "need", "needs", "including", "across", "within",
}


def find_topic_dir(slug):
    """Find topic directory by slug or folder name."""
    for name in os.listdir(TOPICS_DIR):
        path = os.path.join(TOPICS_DIR, name)
        if not os.path.isdir(path):
            continue
        if name == slug:
            return path
        if name.lower().replace(" ", "-") == slug.lower().replace(" ", "-"):
            return path
    return None


def tokenize(text):
    """Simple word tokenization for TF-IDF."""
    words = re.findall(r"[a-z][a-z'-]*[a-z]|[a-z]", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def extract_segments(raw_dir):
    """Extract relevant segments from all raw files."""
    segments = []
    for filepath in sorted(glob.glob(os.path.join(raw_dir, "source-*-raw.yaml"))):
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        source_id = data.get("source_id", "")
        source_title = data.get("title", "")
        for seg in data.get("segments", []):
            if seg.get("type") in RELEVANT_TYPES:
                segments.append({
                    "source_id": source_id,
                    "seg_id": seg["id"],
                    "text": seg["text"],
                    "type": seg["type"],
                    "section": seg.get("section", ""),
                    "source_title": source_title,
                    "metadata": seg.get("metadata"),
                })
    return segments


def build_tfidf(segments):
    """Build TF-IDF vectors for all segments."""
    # Document frequency
    df = Counter()
    doc_tokens = []
    for seg in segments:
        tokens = set(tokenize(seg["text"]))
        doc_tokens.append(tokens)
        for t in tokens:
            df[t] += 1

    n_docs = len(segments)
    # IDF
    idf = {}
    for term, freq in df.items():
        idf[term] = math.log(n_docs / (1 + freq))

    # TF-IDF vectors (sparse, as dicts)
    vectors = []
    for tokens in doc_tokens:
        tf = Counter(tokens)
        vec = {}
        norm = 0.0
        for t in tf:
            val = tf[t] * idf.get(t, 0)
            if val > 0:
                vec[t] = val
                norm += val * val
        norm = math.sqrt(norm) if norm > 0 else 1.0
        # Normalize
        for t in vec:
            vec[t] /= norm
        vectors.append(vec)

    return vectors


def cosine_similarity(v1, v2):
    """Cosine similarity between two sparse vectors (dicts)."""
    if not v1 or not v2:
        return 0.0
    common = set(v1.keys()) & set(v2.keys())
    if not common:
        return 0.0
    return sum(v1[k] * v2[k] for k in common)


def cluster_segments(segments, vectors, threshold=0.15, min_cluster=2):
    """Simple greedy clustering by cosine similarity.

    For each segment, find the most similar existing cluster centroid.
    If similarity > threshold, add to that cluster. Otherwise start a new one.
    """
    clusters = []  # Each cluster: {"centroid": vector, "members": [indices]}

    for i, vec in enumerate(vectors):
        best_sim = -1
        best_cluster = -1
        for c_idx, cluster in enumerate(clusters):
            sim = cosine_similarity(vec, cluster["centroid"])
            if sim > best_sim:
                best_sim = sim
                best_cluster = c_idx

        if best_sim >= threshold and best_cluster >= 0:
            clusters[best_cluster]["members"].append(i)
            # Update centroid (running average)
            centroid = clusters[best_cluster]["centroid"]
            n = len(clusters[best_cluster]["members"])
            for term in vec:
                centroid[term] = centroid.get(term, 0) * ((n - 1) / n) + vec[term] / n
        else:
            clusters.append({"centroid": dict(vec), "members": [i]})

    # Split into multi-source clusters and singles
    multi = []
    singles = []
    for cluster in clusters:
        sources = set(segments[i]["source_id"] for i in cluster["members"])
        if len(cluster["members"]) >= min_cluster and len(sources) >= 2:
            multi.append(cluster)
        else:
            singles.append(cluster)

    return multi, singles


def label_cluster(segments, member_indices):
    """Generate a short label for a cluster from its most common terms."""
    all_tokens = Counter()
    for i in member_indices:
        tokens = tokenize(segments[i]["text"])
        all_tokens.update(tokens)
    top = all_tokens.most_common(5)
    return "_".join(t for t, _ in top[:3])


def build_output(segments, multi_clusters, single_clusters, topic_title):
    """Build the alignment-input YAML structure."""
    output = {
        "meta": {
            "topic": topic_title,
            "total_raw_segments": None,  # filled below
            "relevant_segments": len(segments),
            "clusters": len(multi_clusters),
            "unclustered_segments": sum(
                len(c["members"]) for c in single_clusters
            ),
        },
        "clusters": [],
        "unclustered": [],
    }

    # Multi-source clusters (candidate canonical claims)
    for c_idx, cluster in enumerate(multi_clusters):
        sources = set()
        members = []
        for i in cluster["members"]:
            seg = segments[i]
            sources.add(seg["source_id"])
            entry = {
                "source_id": seg["source_id"],
                "seg_id": seg["seg_id"],
                "type": seg["type"],
                "text": seg["text"],
            }
            if seg.get("metadata"):
                entry["metadata"] = seg["metadata"]
            members.append(entry)

        label = label_cluster(segments, cluster["members"])
        output["clusters"].append({
            "cluster_id": f"cl-{c_idx + 1:03d}",
            "label": label,
            "source_count": len(sources),
            "segment_count": len(members),
            "segments": members,
        })

    # Sort clusters by source_count descending
    output["clusters"].sort(key=lambda c: (-c["source_count"], -c["segment_count"]))

    # Unclustered segments (candidates for unique claims)
    for cluster in single_clusters:
        for i in cluster["members"]:
            seg = segments[i]
            entry = {
                "source_id": seg["source_id"],
                "seg_id": seg["seg_id"],
                "type": seg["type"],
                "text": seg["text"],
            }
            if seg.get("metadata"):
                entry["metadata"] = seg["metadata"]
            output["unclustered"].append(entry)

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Pre-process raw segments for claim alignment"
    )
    parser.add_argument("topic", help="Topic slug or name")
    parser.add_argument(
        "--threshold", type=float, default=0.15,
        help="Cosine similarity threshold for clustering (default: 0.15)"
    )
    parser.add_argument(
        "--min-cluster", type=int, default=2,
        help="Minimum segments to form a cluster (default: 2)"
    )
    args = parser.parse_args()

    topic_dir = find_topic_dir(args.topic)
    if not topic_dir:
        print(f"Error: Topic '{args.topic}' not found in {TOPICS_DIR}")
        sys.exit(1)

    topic_name = os.path.basename(topic_dir)

    # Load topic title
    index_path = os.path.join(topic_dir, "_index.md")
    topic_title = topic_name
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            content = f.read()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1])
                    topic_title = meta.get("title", topic_name)
                except yaml.YAMLError:
                    pass

    raw_dir = os.path.join(topic_dir, "raw")
    extractions_dir = os.path.join(topic_dir, "extractions")
    os.makedirs(extractions_dir, exist_ok=True)

    print(f"Topic: {topic_title}")
    print(f"Raw directory: {raw_dir}")

    # Count total segments for stats
    total_segments = 0
    for filepath in glob.glob(os.path.join(raw_dir, "source-*-raw.yaml")):
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        if data:
            total_segments += data.get("total_segments", 0)

    # Extract relevant segments
    segments = extract_segments(raw_dir)
    print(f"\nTotal segments in raw files: {total_segments}")
    print(f"Relevant segments extracted: {len(segments)} "
          f"({len(segments)/total_segments*100:.1f}%)")
    print(f"Filtered out: {total_segments - len(segments)} "
          f"(noise, context, definition, methodology, etc.)")

    if not segments:
        print("No relevant segments found.")
        sys.exit(1)

    # Count sources
    source_ids = set(s["source_id"] for s in segments)
    print(f"Sources with relevant segments: {len(source_ids)}")

    # Type breakdown
    type_counts = Counter(s["type"] for s in segments)
    print(f"Type breakdown: " + ", ".join(
        f"{t}:{c}" for t, c in type_counts.most_common()
    ))

    # Build TF-IDF and cluster
    print(f"\nBuilding TF-IDF vectors...")
    vectors = build_tfidf(segments)

    print(f"Clustering (threshold={args.threshold}, min_cluster={args.min_cluster})...")
    multi, singles = cluster_segments(
        segments, vectors,
        threshold=args.threshold,
        min_cluster=args.min_cluster,
    )

    multi_segs = sum(len(c["members"]) for c in multi)
    single_segs = sum(len(c["members"]) for c in singles)
    print(f"\nResults:")
    print(f"  Theme clusters: {len(multi)} ({multi_segs} segments)")
    print(f"  Unclustered: {single_segs} segments (candidates for unique claims)")

    # Build output
    output = build_output(segments, multi, singles, topic_title)
    output["meta"]["total_raw_segments"] = total_segments

    # Write
    output_path = os.path.join(extractions_dir, "alignment-input.yaml")
    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True, width=200)

    # Stats
    output_size = os.path.getsize(output_path)
    raw_size = sum(
        os.path.getsize(fp)
        for fp in glob.glob(os.path.join(raw_dir, "source-*-raw.yaml"))
    )
    reduction = (1 - output_size / raw_size) * 100 if raw_size > 0 else 0

    print(f"\nWritten: {output_path}")
    print(f"  Raw input size: {raw_size:,} bytes")
    print(f"  Alignment input size: {output_size:,} bytes")
    print(f"  Reduction: {reduction:.1f}%")

    # Top clusters preview
    print(f"\nTop 10 clusters by source coverage:")
    for cluster in output["clusters"][:10]:
        print(f"  {cluster['cluster_id']} [{cluster['source_count']} sources, "
              f"{cluster['segment_count']} segs] {cluster['label']}")


if __name__ == "__main__":
    main()
