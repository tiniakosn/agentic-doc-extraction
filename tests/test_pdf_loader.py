
import pymupdf

from src.ingestion.pdf_loader import extract_digital_regions


def test_digital_regions_clip_normalized_bbox():
    path = "data/discovery/63ΤΞ46ΜΦΟΤ-ΑΟΟ.pdf"

    with pymupdf.open(path) as pdf:
        regions = extract_digital_regions(pdf[0])

    assert regions

    for region in regions:
        bbox = region.normalized_bbox

        if bbox is None:
            continue

        x1, y1, x2, y2 = bbox

        assert 0 <= x1 < x2 <= 1
        assert 0 <= y1 < y2 <= 1

    assert regions[47].normalized_bbox[2] == 1.0
