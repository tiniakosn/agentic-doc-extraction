from src.ingestion.page_quality import count_unassigned_chars


def test_unassigned_unicode_detection():
    healthy = "ΚΕΝΤΡΟ ΕΚΠΑΙΔΕΥΣΗΣ ΝΑΥΤΙΚΗΣ ΑΠΟΤΡΟΠΗΣ"
    corrupted = "ΚΕΝΣΡΟ ΕΚΠΑΘΔΕΤ\u03a2Η\u03a2"

    assert count_unassigned_chars(healthy) == 0
    assert count_unassigned_chars(corrupted) == 2


def test_empty_text_has_no_unassigned_chars():
    assert count_unassigned_chars("") == 0


from src.ingestion.page_quality import PageQuality
from src.ingestion.routing import choose_processing_route_v2


def test_unassigned_unicode_triggers_ocr():
    quality = PageQuality(
        text_chars=1800,
        image_count=0,
        image_coverage=0.0,
        suspicious_text_ratio=0.0,
        visual_ink_ratio=0.06,
        greek_letter_ratio=0.89,
        unassigned_char_count=15,
    )

    decision = choose_processing_route_v2(quality)

    assert decision.route == "tesseract"


def test_healthy_digital_text_remains_digital():
    quality = PageQuality(
        text_chars=2300,
        image_count=0,
        image_coverage=0.0,
        suspicious_text_ratio=0.0,
        visual_ink_ratio=0.09,
        greek_letter_ratio=0.93,
        unassigned_char_count=0,
    )

    decision = choose_processing_route_v2(quality)

    assert decision.route == "digital"
