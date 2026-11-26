

def test_opening_lint_flags_a_crowded_cold_open_and_an_early_welcome():
    from pipeline.script_format import lint_opening
    bad = """[Section: Opening]
[Face]
Microsoft has some of the most advanced AI in the world. So how did its email, its meetings and its AI assistant go down for days?
[Visual: title The Biggest IPO]
This week also brought the largest IPO in history, and Gulf investors made big paper gains from it.
[Visual: title California vs. OpenAI]
California is suing OpenAI over AI safety. And Google and Alibaba are fighting a price war on AI models.
Let's get into it.

[Section: Welcome]
Hi everyone, welcome to AI This Week. I'm Wissam Kishek. I've spent 25 years in enterprise software, across the Middle East.

[Section: The Day Microsoft Stopped]
Let's start with the full story.
"""
    rules = {f.rule for f in lint_opening(bad)}
    assert rules == {"hook-words", "hook-cards", "welcome-first", "welcome-words"}


def test_opening_lint_passes_a_short_hook_and_a_welcome_after_the_first_story():
    from pipeline.script_format import lint_opening
    good = """[Section: Opening]
Microsoft's email and AI assistant went down for days. In Britain, hospitals went back to paper.
How much of your company runs on one provider? Also coming: a record IPO and a lawsuit against OpenAI.

[Section: The Day Microsoft Stopped]
The outage began on Monday, Reuters reports, and lasted three days.
Hi everyone, welcome to AI This Week, I'm Wissam.

[Section: The IPO]
Next, the listing.
"""
    assert lint_opening(good) == []
