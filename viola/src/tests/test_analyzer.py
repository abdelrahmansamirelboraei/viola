from viola.analyzers.emotion_distortion import EmotionDistortionAnalyzer

def test_analyzer_detects_anxiety_and_distortion():
    a = EmotionDistortionAnalyzer().analyze("انا قلقان ومش قادر اركز وحاسس اني دايمًا هفشل")
    names_emo = [e.name for e in a.emotions]
    names_dis = [d.name for d in a.distortions]

    assert "anxiety" in names_emo
    # overgeneralization OR fortune_telling are both acceptable depending on patterns
    assert ("overgeneralization" in names_dis) or ("fortune_telling" in names_dis)

def test_analyzer_crisis_flag():
    a = EmotionDistortionAnalyzer().analyze("مش قادر اكمل وحياتي ملهاش لازمه")
    assert a.crisis_flag is True
    assert len(a.crisis_signals) >= 1
