from pipeline.post.subtitles import Word
from pipeline.video.ownvoice import retakes, stretches


def ws(text, t0):
    return [Word(t0 + i * 0.4, t0 + i * 0.4 + 0.3, w) for i, w in enumerate(text.split())]


def test_abandoned_take_is_cut_and_the_last_kept():
    words = ws("حسب رويترز أدنوك ومجموعة", 0) + ws("حسب رويترز أدنوك ومجموعة جي فورتي تو وقعوا صفقة", 4) \
        + ws("والصفقة إجت بنفس الوقت", 12)
    parts = stretches(words)
    assert len(parts) == 3 and retakes(parts) == {0}


def test_different_sentences_are_kept():
    words = ws("خلينا نبلش من الخليج", 0) + ws("حسب رويترز أدنوك وقعت", 4) + ws("ياهو فاينانس وصفت الاتفاق", 8)
    assert retakes(stretches(words)) == set()


def test_phrase_said_twice_cuts_the_first():
    from pipeline.video.ownvoice import _minus, repeat_cuts
    words = ws("الفكرة بسيطة وكيل واحد وكيل واحد وأداتين إشي", 0)
    cuts = repeat_cuts(words, ["وكيل واحد وأداتين"])
    assert len(cuts) == 1 and cuts[0][0] == words[2].start and cuts[0][1] == words[4].start
    assert _minus([(0.0, 10.0)], [(1.0, 2.0)]) == [(0.0, 1.0), (2.0, 10.0)]
