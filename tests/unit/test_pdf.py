"""Tests for PDF extractor helper functions."""

from __future__ import annotations

import pytest

from insight.collector.pdf import _merge_nearby_rects, _find_figure_regions


# --- _merge_nearby_rects ---


class TestMergeNearbyRects:
    def test_empty_input(self):
        assert _merge_nearby_rects([]) == []

    def test_single_rect(self):
        result = _merge_nearby_rects([(10, 20, 100, 200)])
        assert len(result) == 1
        assert result[0] == (10, 20, 100, 200)

    def test_two_overlapping_rects(self):
        rects = [(10, 10, 50, 50), (30, 30, 80, 80)]
        result = _merge_nearby_rects(rects, gap=0)
        assert len(result) == 1
        assert result[0] == (10, 10, 80, 80)

    def test_two_nearby_rects_within_gap(self):
        # 5px apart, gap=10 → should merge
        rects = [(10, 10, 50, 50), (55, 10, 100, 50)]
        result = _merge_nearby_rects(rects, gap=10)
        assert len(result) == 1
        assert result[0] == (10, 10, 100, 50)

    def test_two_distant_rects_stay_separate(self):
        # 50px apart, gap=10 → should NOT merge
        rects = [(10, 10, 50, 50), (100, 100, 200, 200)]
        result = _merge_nearby_rects(rects, gap=10)
        assert len(result) == 2

    def test_chain_merge(self):
        # A overlaps B, B overlaps C, A doesn't overlap C → all merged
        rects = [(10, 10, 30, 30), (25, 25, 50, 50), (45, 45, 70, 70)]
        result = _merge_nearby_rects(rects, gap=0)
        assert len(result) == 1
        assert result[0] == (10, 10, 70, 70)

    def test_two_clusters(self):
        # Cluster 1: two rects overlapping
        # Cluster 2: one rect far away
        rects = [
            (10, 10, 50, 50),
            (40, 40, 80, 80),
            (300, 300, 400, 400),
        ]
        result = _merge_nearby_rects(rects, gap=5)
        assert len(result) == 2
        bboxes = sorted(result)
        assert bboxes[0] == (10, 10, 80, 80)
        assert bboxes[1] == (300, 300, 400, 400)

    def test_vertical_gap_merge(self):
        # Stacked vertically, within gap
        rects = [(10, 10, 50, 50), (10, 55, 50, 100)]
        result = _merge_nearby_rects(rects, gap=10)
        assert len(result) == 1
        assert result[0] == (10, 10, 50, 100)

    def test_exact_gap_boundary(self):
        # Exactly gap pixels apart → should merge (gap is inclusive)
        rects = [(10, 10, 50, 50), (60, 10, 100, 50)]
        result = _merge_nearby_rects(rects, gap=10)
        assert len(result) == 1

    def test_just_beyond_gap(self):
        # 11px apart, gap=10 → should NOT merge
        rects = [(10, 10, 50, 50), (61, 10, 100, 50)]
        result = _merge_nearby_rects(rects, gap=10)
        assert len(result) == 2


# --- _find_figure_regions ---


class FakePage:
    """Minimal mock of a PyMuPDF Page for testing _find_figure_regions."""

    def __init__(self, drawings, width=612, height=792, text_blocks=None):
        self._drawings = drawings
        self._text_blocks = text_blocks or []
        self.rect = FakeRect(0, 0, width, height)

    def get_drawings(self):
        return self._drawings

    def get_text(self, mode="text"):
        if mode == "dict":
            return {"blocks": self._text_blocks}
        return ""


class FakeRect:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1
        self.width = x1 - x0
        self.height = y1 - y0


class TestFindFigureRegions:
    def test_no_drawings(self):
        page = FakePage([])
        assert _find_figure_regions(page) == []

    def test_too_few_drawings(self):
        # Less than 5 rects → no figures detected
        drawings = [{"rect": (100, 100, 200, 200)}] * 4
        page = FakePage(drawings)
        assert _find_figure_regions(page) == []

    def test_single_figure_cluster(self):
        # 10 nearby drawings forming one figure
        drawings = [
            {"rect": (100 + i * 5, 100, 130 + i * 5, 150)}
            for i in range(10)
        ]
        page = FakePage(drawings)
        regions = _find_figure_regions(page, min_area=500, padding=10)
        assert len(regions) == 1
        x0, y0, x1, y1 = regions[0]
        # Should cover from first to last drawing, with padding
        assert x0 <= 100
        assert y0 <= 100
        assert x1 >= 175  # last drawing ends at 130+45=175
        assert y1 >= 150

    def test_two_separate_figures(self):
        # Two clusters of drawings far apart
        cluster1 = [{"rect": (50 + i * 5, 50, 80 + i * 5, 100)} for i in range(6)]
        cluster2 = [{"rect": (400 + i * 5, 500, 430 + i * 5, 600)} for i in range(6)]
        page = FakePage(cluster1 + cluster2)
        regions = _find_figure_regions(page, min_area=500, padding=5)
        assert len(regions) == 2

    def test_filters_thin_horizontal_bars(self):
        # Full-width thin bar (page decoration) should be filtered
        drawings = [{"rect": (10, 100, 600, 105)}] * 10  # thin horizontal
        page = FakePage(drawings, width=612, height=792)
        regions = _find_figure_regions(page, min_area=100, padding=5)
        assert len(regions) == 0

    def test_filters_tiny_decorations(self):
        # Small scattered dots below min_area
        drawings = [{"rect": (i * 50, 100, i * 50 + 5, 105)} for i in range(10)]
        page = FakePage(drawings)
        regions = _find_figure_regions(page, min_area=5000, padding=5)
        assert len(regions) == 0

    def test_skips_raster_overlap(self):
        # A vector region that overlaps with an already-extracted raster image
        drawings = [{"rect": (100 + i * 5, 100, 130 + i * 5, 300)} for i in range(10)]
        page = FakePage(drawings)
        raster_rects = [(90, 90, 200, 310)]  # covers most of the drawing cluster
        regions = _find_figure_regions(
            page, raster_rects=raster_rects, min_area=500, padding=5,
        )
        assert len(regions) == 0

    def test_keeps_region_without_raster_overlap(self):
        drawings = [{"rect": (100 + i * 5, 100, 130 + i * 5, 300)} for i in range(10)]
        page = FakePage(drawings)
        raster_rects = [(500, 500, 600, 600)]  # far away
        regions = _find_figure_regions(
            page, raster_rects=raster_rects, min_area=500, padding=5,
        )
        assert len(regions) == 1

    def test_clips_to_page_bounds(self):
        # Drawings near page edge — padding should not exceed page bounds
        drawings = [{"rect": (0 + i, 0, 10 + i, 200)} for i in range(10)]
        page = FakePage(drawings, width=612, height=792)
        regions = _find_figure_regions(page, min_area=500, padding=20)
        assert len(regions) == 1
        x0, y0, x1, y1 = regions[0]
        assert x0 >= 0
        assert y0 >= 0

    def test_filters_text_heavy_regions(self):
        # A region with lots of text inside is a styled text container, not a figure
        drawings = [{"rect": (100 + i * 5, 100, 130 + i * 5, 300)} for i in range(10)]
        text_blocks = [
            {"type": 0, "bbox": (105, 110, 170, 290)},  # large text block inside region
        ]
        page = FakePage(drawings, text_blocks=text_blocks)
        # With text covering ~50% of the region → filtered out (default max=0.3)
        regions = _find_figure_regions(page, min_area=500, padding=5)
        assert len(regions) == 0

    def test_keeps_low_text_regions(self):
        # A region with minimal text (axis labels) should be kept
        drawings = [{"rect": (100 + i * 5, 100, 130 + i * 5, 300)} for i in range(10)]
        text_blocks = [
            {"type": 0, "bbox": (105, 280, 140, 295)},  # small label
        ]
        page = FakePage(drawings, text_blocks=text_blocks)
        regions = _find_figure_regions(page, min_area=500, padding=5)
        assert len(regions) == 1

    def test_filters_low_drawing_count(self):
        # Regions with only 1-2 drawings (card backgrounds) should be filtered
        # 3 widely spaced rectangles — each forms its own cluster with 1 drawing
        drawings = [
            {"rect": (100, 100, 300, 300)},  # 1 big rect
            {"rect": (100, 400, 300, 600)},  # another
            {"rect": (100, 700, 300, 900)},  # third
            {"rect": (400, 100, 600, 300)},  # fourth
            {"rect": (400, 400, 600, 600)},  # fifth — needed to pass len(rects) >= 5
        ]
        page = FakePage(drawings, width=700, height=1000)
        # Each cluster has only 1 drawing → filtered by min_drawings=5
        regions = _find_figure_regions(page, min_area=500, padding=5)
        assert len(regions) == 0

    def test_skips_degenerate_drawings(self):
        # Drawings with zero width/height are ignored
        drawings = [
            {"rect": (100, 100, 100, 200)},  # zero width
            {"rect": (100, 100, 200, 100)},  # zero height
            {"rect": None},  # no rect
        ] + [{"rect": (200 + i * 5, 200, 230 + i * 5, 400)} for i in range(8)]
        page = FakePage(drawings)
        regions = _find_figure_regions(page, min_area=500, padding=5)
        # Only the valid cluster of 8 should form a region
        assert len(regions) == 1
