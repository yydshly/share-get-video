"""
tests/test_ai_asset_image_retry.py
Loop1: AI素材路线背景图生成瞬时失败时重试，避免无谓回退渐变拉低探测表现。
"""

from app.video_lab.renderers.visual.ai_asset_renderer import _generate_image_with_retry


class _FakeClient:
    """按预设结果序列返回，记录调用次数。"""

    def __init__(self, results):
        self._results = list(results)
        self.calls = 0

    def generate(self, prompt, path, aspect_ratio="9:16"):
        self.calls += 1
        return self._results[min(self.calls - 1, len(self._results) - 1)]


def test_retry_recovers_after_transient_failure():
    """第一次失败、第二次成功 → 返回成功，且确实重试了一次。"""
    client = _FakeClient([
        {"success": False, "providerMessage": "timeout"},
        {"success": True, "providerMessage": "Success"},
    ])
    r = _generate_image_with_retry(client, "p", "x.png", "9:16", attempts=2)
    assert r["success"] is True
    assert client.calls == 2


def test_no_retry_when_first_succeeds():
    """第一次就成功 → 不浪费第二次调用。"""
    client = _FakeClient([{"success": True}])
    r = _generate_image_with_retry(client, "p", "x.png", "9:16", attempts=2)
    assert r["success"] is True
    assert client.calls == 1


def test_returns_last_failure_when_all_fail():
    """全部失败 → 返回最后一次失败结果（供上层回退渐变）。"""
    client = _FakeClient([
        {"success": False, "providerMessage": "e1"},
        {"success": False, "providerMessage": "e2"},
    ])
    r = _generate_image_with_retry(client, "p", "x.png", "9:16", attempts=2)
    assert r["success"] is False
    assert r["providerMessage"] == "e2"
    assert client.calls == 2


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
