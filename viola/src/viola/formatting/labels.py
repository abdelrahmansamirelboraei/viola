from __future__ import annotations

# English label -> Arabic label
EMOTIONS_AR = {
    "anxiety": "قلق/توتر",
    "sadness": "حزن",
    "anger": "غضب",
    "self_blame": "لوم الذات",
    "hopelessness": "يأس",
    "shame": "خجل/عار",
}

DISTORTIONS_AR = {
    "catastrophizing": "تهويل/توقع الأسوأ",
    "overgeneralization": "تعميم مفرط (دايمًا/أبدًا)",
    "mind_reading": "قراءة أفكار الآخرين",
    "fortune_telling": "تنبؤ سلبي بالمستقبل",
    "should_statements": "لازم/مفروض (جلد الذات)",
    "labeling": "وضع ملصقات على الذات",
    "all_or_nothing": "تفكير أبيض/أسود",
}

def emo_ar(key: str) -> str:
    return EMOTIONS_AR.get(key, key)

def dist_ar(key: str) -> str:
    return DISTORTIONS_AR.get(key, key)
