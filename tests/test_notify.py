from scripts.notify import whatsapp


class R:
    def __init__(self, code): self.status_code = code


class Http:
    def __init__(self, code=200): self.code, self.calls = code, []
    def get(self, url, params, timeout):
        self.calls.append(params)
        return R(self.code)


def test_off_without_secrets(monkeypatch):
    monkeypatch.delenv("WHATSAPP_PHONE", raising=False)
    monkeypatch.delenv("CALLMEBOT_APIKEY", raising=False)
    h = Http()
    assert whatsapp("hi", http=h) is False and h.calls == []


def test_sends_and_never_raises(monkeypatch):
    monkeypatch.setenv("WHATSAPP_PHONE", "+971500000000")
    monkeypatch.setenv("CALLMEBOT_APIKEY", "k")
    h = Http()
    assert whatsapp("x" * 2000, http=h) is True
    assert h.calls[0]["phone"] == "+971500000000" and len(h.calls[0]["text"]) == 900
    assert whatsapp("hi", http=Http(500)) is False

    class Boom:
        def get(self, *a, **k): raise OSError("down")
    assert whatsapp("hi", http=Boom()) is False
