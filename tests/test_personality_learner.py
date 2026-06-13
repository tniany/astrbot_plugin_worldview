def test_learner_generates_style_hint():
    from main import PersonalityLearner

    learner = PersonalityLearner(window_size=3)
    messages = [
        "哈哈哈这也太逗了",
        "okk 懂了",
        "明天见～",
    ]
    hint = learner.generate_hint(messages)
    assert isinstance(hint, str)
    assert len(hint) > 0


def test_learner_returns_empty_for_few_messages():
    from main import PersonalityLearner

    learner = PersonalityLearner(window_size=3)
    hint = learner.generate_hint(["你好"])
    assert hint == ""
