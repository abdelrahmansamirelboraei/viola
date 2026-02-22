from __future__ import annotations

import re
from typing import Dict, List


# NOTE: Starter + expanded dialect lexicon for Arabic (EG/LEV/GULF).
# Keep patterns short and common; normalization already helps (أ/إ/آ -> ا, ة->ه, ى->ي, removes diacritics).

EMOTION_PATTERNS: Dict[str, List[str]] = {
    "anxiety": [
        # MSA / common
        r"\bقلقان\b", r"\bقلق\b", r"\bمتوتر\b", r"\bتوتر\b", r"\bخايف\b", r"\bمرعوب\b", r"\bمضطرب\b",
        r"\bهلع\b", r"\bنوبه هلع\b", r"\bpanic\b",
        # Egyptian
        r"\bمزنوق\b", r"\bمخنوق\b", r"\bمقلق\b",
        # Levant
        r"\bمتدايق\b", r"\bمو مرتاح\b", r"\bقلبي عم يدق\b",
        # Gulf
        r"\bمضغوط\b", r"\bموتّر\b",
        # function symptoms
        r"\bمش قادر اركز\b", r"\bمش قادر انام\b", r"\bارهاق\b"
    ],
    "sadness": [
        r"\bحزين\b", r"\bزعلان\b", r"\bمكتئب\b", r"\bاكتئاب\b", r"\bمكسور\b", r"\bمنكسر\b",
        # Egyptian
        r"\bمخنوق\b", r"\bمضايق\b", r"\bزهقان\b", r"\bمتبهدل\b",
        # Levant
        r"\bمقهور\b", r"\bمدايق\b",
        # Gulf
        r"\bمكتوم\b", r"\bكئيب\b",
        # crying
        r"\bعايط\b", r"\bبعيط\b", r"\bدموعي\b"
    ],
    "anger": [
        r"\bغضبان\b", r"\bغضب\b", r"\bمتعصب\b", r"\bمعصب\b", r"\bمستفز\b", r"\bمتنرفز\b",
        # Egyptian
        r"\bمجنون\b", r"\bنفسي اكسر\b", r"\bهفرقع\b",
        # Levant
        r"\bمقهور\b", r"\bمعصّب\b",
        # Gulf
        r"\bزعلان مره\b", r"\bمنرفز\b"
    ],
    "self_blame": [
        r"\bانا السبب\b", r"\bغلطتي\b", r"\bذنبى\b", r"\bذنب\b",
        r"\bانا وحش\b", r"\bانا فاشل\b", r"\bمش نافع\b", r"\bبكره نفسي\b", r"\bبلوم نفسي\b",
        # Dialect variants
        r"\bانا الغلطان\b", r"\bانا مقصر\b", r"\bانا قليل\b"
    ],
    "hopelessness": [
        r"\bمفيش امل\b", r"\bلا امل\b", r"\bميؤوس\b", r"\bمستحيل\b",
        r"\bمش هتظبط\b", r"\bمش هينفع\b", r"\bمش هنجح\b", r"\bاكيد هفشل\b",
        # Egyptian / common
        r"\bملهاش لازمه\b", r"\bمش فارقه\b", r"\bخلاص\b",
        # Levant
        r"\bما في فايده\b", r"\bمو نافعه\b",
        # Gulf
        r"\bما منه فايده\b", r"\bمعد له فايده\b"
    ],
    "shame": [
        r"\bمكسوف\b", r"\bاحراج\b", r"\bعار\b", r"\bخجل\b", r"\bفضيحه\b",
        r"\bحاسس بالذنب\b"
    ],
}

DISTORTION_PATTERNS: Dict[str, List[str]] = {
    "catastrophizing": [
        r"\bكارثه\b", r"\bمصيبه\b", r"\bهتدمر\b", r"\bهتخرب\b", r"\bهتبقى نهايه\b", r"\bالنهايه\b",
        r"\bهيحصل اسوا\b", r"\bاسوا حاجه\b", r"\bمش هقدر ابدا\b"
    ],
    "overgeneralization": [
        r"\bدايم[اًا]\b", r"\bابدا\b", r"\bكل مره\b", r"\bعمري ما\b",
        r"\bولا مره\b", r"\bعلى طول\b"
    ],
    "mind_reading": [
        r"\bاكيد شايفني\b", r"\bاكيد بيكرهني\b", r"\bاكيد فكرني\b", r"\bالناس فاكراني\b",
        r"\bعارف انهم\b", r"\bهم شايفين\b", r"\bهم مفكرين\b"
    ],
    "fortune_telling": [
        r"\bاكيد هفشل\b", r"\bمش هنجح\b", r"\bهخسر\b", r"\bمش هيحصل\b", r"\bمش هتظبط\b", r"\bمش هينفع\b"
    ],
    "should_statements": [
        r"\bلازم\b", r"\bمفروض\b", r"\bكان لازم\b", r"\bكان مفروض\b", r"\bينبغي\b"
    ],
    "labeling": [
        r"\bانا فاشل\b", r"\bانا غبي\b", r"\bانا عديم\b", r"\bانا قليل\b", r"\bانا ولا حاجه\b"
    ],
    "all_or_nothing": [
        r"\bيا اما\b", r"\bابيض او اسود\b", r"\bكله أو لا شيء\b", r"\bاما كامل اما فاشل\b"
    ],
}

CRISIS_PATTERNS: List[str] = [
    r"\bعايز اموت\b",
    r"\bعايز انتحر\b",
    r"\bهنهي حياتي\b",
    r"\bمش عايز اعيش\b",
    r"\bهاذي نفسي\b",
    r"\bحياتي ملهاش لازمه\b",
    r"\bمش قادر اكمل\b",
    r"\bتعبت من العيشه\b",
]

def compile_patterns(patterns: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
    return {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in patterns.items()}

COMPILED_EMOTIONS = compile_patterns(EMOTION_PATTERNS)
COMPILED_DISTORTIONS = compile_patterns(DISTORTION_PATTERNS)
COMPILED_CRISIS = [re.compile(p, re.IGNORECASE) for p in CRISIS_PATTERNS]
