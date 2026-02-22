from viola.text.normalizer import normalize_arabic

def test_normalize_arabic_basic():
    s = "إنتَ قلقان؟؟ ومش قادِر أركّز!!!"
    n = normalize_arabic(s)
    # After normalization: hamza/alef forms -> ا, diacritics removed, punctuation collapsed
    assert "قلقان" in n
    assert "مش قادر اركز" in n
