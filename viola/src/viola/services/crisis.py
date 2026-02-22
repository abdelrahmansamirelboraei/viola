from __future__ import annotations

from typing import Any


def crisis_reply_ar(user_text: str, safety_state: dict[str, Any]) -> str:
    # Keep it short and consistent. It must preserve context.
    safe_confirmed = bool(safety_state.get("safe_confirmed", False))

    if not safe_confirmed:
        return (
            "🚨 **Crisis Mode**\n\n"
            "أنا واخد كلامك بجدية. قبل ما نكمل أي موضوع (حتى السفر)، محتاج أتأكد:\n"
            "- هل أنت في خطر فوري الآن أو ناوي تأذي نفسك دلوقتي؟\n"
            "- هل في شخص قريب منك تقدر تكلمه فورًا؟\n\n"
            "لو في خطر فوري: اتصل بالطوارئ الآن.\n"
            "في مصر: 122 (شرطة) أو 123 (إسعاف). في أي بلد تانية: رقم الطوارئ المحلي.\n\n"
            "اكتبلي سطر واحد: **(أنا بأمان الآن / مش بأمان)**."
        )

    # If user confirmed safety, allow gentle transition but still monitor
    return (
        "✅ تمام. هنكمل، بس لو رجعت أفكار الإيذاء تاني قولّي فورًا.\n\n"
        f"قلت: **{user_text}**\n"
        "خلّينا ناخدها خطوة بخطوة: السفر هنا تقصد بيه هروب من ضغط/بيئة؟ ولا خطة فعلية (بلد/مدة/هدف)؟"
    )
