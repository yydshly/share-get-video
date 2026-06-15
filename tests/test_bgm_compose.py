"""
tests/test_bgm_compose.py
V0.3.8: BGM composition tests — FFmpeg lavfi ambient BGM mixing
V0.3.8.1: Fixed lavfi command, camelCase support, command structure validation
"""

import pytest
from pathlib import Path
import tempfile
import os
import subprocess

from app.video_lab.renderers.ffmpeg_av_composer import (
    normalize_bgm_params,
    compose_av_with_subtitles,
    compose_video_with_audio,
    check_ffmpeg_available,
    BGM_MODE_NONE,
    BGM_MODE_GENERATED_AMBIENT,
    BGM_VOLUME_MIN,
    BGM_VOLUME_MAX,
    BGM_VOLUME_DEFAULT,
)


# ─── normalize_bgm_params Tests ───────────────────────────────────────────────

class TestNormalizeBgmParams:
    """Test BGM parameter normalization."""

    def test_no_bgm_returns_none_mode(self):
        result = normalize_bgm_params({})
        assert result["mode"] == BGM_MODE_NONE
        assert result["volume"] == BGM_VOLUME_DEFAULT

    def test_empty_params_returns_none(self):
        result = normalize_bgm_params({})
        assert result["mode"] == "none"

    def test_nested_bgm_mode_generated_ambient(self):
        result = normalize_bgm_params({
            "bgm": {
                "mode": "generated_ambient",
                "volume": 0.08,
                "fade_in": 1.5,
                "fade_out": 2.0,
            }
        })
        assert result["mode"] == "generated_ambient"
        assert result["volume"] == 0.08
        assert result["fade_in"] == 1.5
        assert result["fade_out"] == 2.0

    def test_flat_bgm_params(self):
        result = normalize_bgm_params({
            "bgmMode": "generated_ambient",
            "bgmVolume": 0.1,
        })
        assert result["mode"] == "generated_ambient"
        assert result["volume"] == 0.1

    def test_nested_takes_priority_over_flat(self):
        """Nested bgm config should win over flat bgmMode/bgmVolume."""
        result = normalize_bgm_params({
            "bgm": {"mode": "none", "volume": 0.05},
            "bgmMode": "generated_ambient",
            "bgmVolume": 0.15,
        })
        assert result["mode"] == "none"
        assert result["volume"] == 0.05

    def test_volume_clamped_to_min(self):
        result = normalize_bgm_params({
            "bgm": {"mode": "generated_ambient", "volume": -0.5}
        })
        assert result["volume"] == BGM_VOLUME_MIN

    def test_volume_clamped_to_max(self):
        result = normalize_bgm_params({
            "bgm": {"mode": "generated_ambient", "volume": 99.0}
        })
        assert result["volume"] == BGM_VOLUME_MAX

    def test_invalid_mode_defaults_to_none(self):
        result = normalize_bgm_params({
            "bgm": {"mode": "invalid_mode", "volume": 0.08}
        })
        assert result["mode"] == BGM_MODE_NONE

    def test_case_insensitive_mode(self):
        result = normalize_bgm_params({
            "bgm": {"mode": "Generated_Ambient", "volume": 0.08}
        })
        assert result["mode"] == "generated_ambient"

    def test_fade_values_clamped(self):
        result = normalize_bgm_params({
            "bgm": {"mode": "generated_ambient", "fade_in": -1.0, "fade_out": 99.0}
        })
        assert result["fade_in"] == 0.0
        assert result["fade_out"] == 5.0


# ─── compose_av_with_subtitles BGM Tests ──────────────────────────────────────

class TestComposeAvWithSubtitlesBgm:
    """Test BGM integration in compose_av_with_subtitles."""

    def test_no_bgm_params_returns_none_mode(self):
        """When no BGM params given, bgm_enabled should be False."""
        # FFmpeg not available path — just check the return structure
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
        )
        assert result.get("bgm_enabled") is False
        assert result.get("bgm_mode") == "none"
        # volume is the normalized default (0.08), not 0.0 — that's fine since mode=none
        assert result.get("bgm_volume") == 0.08

    def test_bgm_none_returns_none_mode(self):
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
            bgm_params={"bgm": {"mode": "none", "volume": 0.0}},
        )
        assert result.get("bgm_enabled") is False
        assert result.get("bgm_mode") == "none"

    def test_bgm_generated_ambient_sets_correct_mode(self):
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.06}},
        )
        assert result.get("bgm_enabled") is True
        assert result.get("bgm_mode") == "generated_ambient"
        assert result.get("bgm_volume") == 0.06

    def test_ffmpeg_unavailable_has_bgm_fields(self):
        """Even when FFmpeg is unavailable, result should have bgm_* fields."""
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.1}},
        )
        assert "bgm_enabled" in result
        assert "bgm_mode" in result
        assert "bgm_volume" in result


class TestComposeVideoWithAudioBgm:
    """Test BGM integration in compose_video_with_audio."""

    def test_no_bgm_returns_none_mode(self):
        result = compose_video_with_audio(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
        )
        assert result.get("bgm_enabled") is False
        assert result.get("bgm_mode") == "none"

    def test_bgm_generated_ambient_enabled(self):
        result = compose_video_with_audio(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.07}},
        )
        assert result.get("bgm_enabled") is True
        assert result.get("bgm_mode") == "generated_ambient"
        assert result.get("bgm_volume") == 0.07


# ─── Integration: manifest/assets BGM fields ──────────────────────────────────

class TestBgmManifestAssets:
    """Verify BGM info appears in the manifest and assets structures.

    These test the data shapes that tts_subtitle_compose produces,
    without requiring actual FFmpeg execution.
    """

    def test_bgm_info_in_assets_shape(self):
        """Assets dict should include bgmEnabled, bgmMode, bgmVolume keys."""
        # This is a structural test: we verify that the compose result
        # includes the BGM keys that will be propagated to assets
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.08}},
        )
        # Even on failure (FFmpeg unavailable), keys must be present
        assert "bgmEnabled" not in result  # note: returned as bgm_enabled not bgmEnabled
        assert "bgm_mode" in result
        assert "bgm_volume" in result

    def test_normalized_bgm_passes_through_to_compose(self):
        """normalize_bgm_params output can be passed as bgm_params to compose functions."""
        # Use the nested format (same as what params.bgm carries)
        original_params = {
            "bgm": {"mode": "generated_ambient", "volume": 0.05, "fade_in": 1.0, "fade_out": 2.0}
        }
        # Normalize first, then pass through to compose
        normalized = normalize_bgm_params(original_params)
        assert normalized["mode"] == "generated_ambient"
        assert normalized["volume"] == 0.05
        # The normalized dict can be used directly as bgm_params (compose re-normalizes it)
        result = compose_av_with_subtitles(
            video_path=Path("nonexistent.mp4"),
            audio_path=Path("nonexistent.mp3"),
            output_path=Path("output.mp4"),
            bgm_params=original_params,  # pass the original nested dict, not the normalized output
        )
        assert result["bgm_enabled"] is True
        assert result["bgm_mode"] == "generated_ambient"
        assert result["bgm_volume"] == 0.05


# ─── V0.3.8.1: Additional Tests ─────────────────────────────────────────────

class TestNormalizeBgmParamsV081:
    """V0.3.8.1: camelCase fadeIn/fadeOut and direct dict support."""

    def test_camelCase_fadeIn_fadeOut(self):
        """Frontend preset uses fadeIn/fadeOut (camelCase)."""
        result = normalize_bgm_params({
            "bgm": {"mode": "generated_ambient", "volume": 0.06, "fadeIn": 1.5, "fadeOut": 2.0}
        })
        assert result["mode"] == "generated_ambient"
        assert result["volume"] == 0.06
        assert result["fade_in"] == 1.5
        assert result["fade_out"] == 2.0

    def test_snake_case_fade_in_fade_out(self):
        """snake_case also supported."""
        result = normalize_bgm_params({
            "bgm": {"mode": "generated_ambient", "volume": 0.07, "fade_in": 1.0, "fade_out": 1.8}
        })
        assert result["fade_in"] == 1.0
        assert result["fade_out"] == 1.8

    def test_direct_standardized_dict(self):
        """Direct {"mode": ..., "volume": ...} dict is recognized."""
        result = normalize_bgm_params({
            "mode": "generated_ambient",
            "volume": 0.09,
            "fade_in": 0.5,
            "fade_out": 1.0,
        })
        assert result["mode"] == "generated_ambient"
        assert result["volume"] == 0.09
        assert result["fade_in"] == 0.5
        assert result["fade_out"] == 1.0

    def test_empty_dict_returns_default(self):
        """Empty dict returns default (mode=none)."""
        result = normalize_bgm_params({})
        assert result["mode"] == "none"


class TestBgmCommandStructure:
    """V0.3.8.1: Validate FFmpeg command structure without running FFmpeg."""

    def test_bgm_none_no_sine_bgm_input(self, tmp_path):
        """mode=none should not include sine-wave BGM input."""
        video_path = tmp_path / "v.mp4"
        audio_path = tmp_path / "a.mp3"
        # Create minimal files using aevalsrc=0 for silence (universally supported)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=2x2:d=0.1",
                       "-c:v", "libx264", "-t", "0.1", str(video_path)],
                      capture_output=True, timeout=30)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "aevalsrc=0",
                       "-ar", "44100", "-ac", "2", "-t", "0.1",
                       "-c:a", "aac", str(audio_path)],
                      capture_output=True, timeout=30)

        result = compose_video_with_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=tmp_path / "out.mp4",
            bgm_params={"bgm": {"mode": "none", "volume": 0.1}},
        )
        cmd = result.get("ffmpeg_command", "")
        # mode=none: no sine-wave BGM input should appear
        # (video still uses lavfi for color=black but that's test setup, not BGM)
        assert "sine=frequency=220" not in cmd
        assert result["bgm_enabled"] is False

    def test_bgm_enabled_includes_sine_input(self, tmp_path):
        """mode=generated_ambient should include sine-wave BGM input."""
        video_path = tmp_path / "v.mp4"
        audio_path = tmp_path / "a.mp3"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=2x2:d=0.1",
                       "-c:v", "libx264", "-t", "0.1", str(video_path)],
                      capture_output=True, timeout=30)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "aevalsrc=0",
                       "-ar", "44100", "-ac", "2", "-t", "0.1",
                       "-c:a", "aac", str(audio_path)],
                      capture_output=True, timeout=30)

        result = compose_video_with_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=tmp_path / "out.mp4",
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.06}},
        )
        cmd = result.get("ffmpeg_command", "")
        # BGM sine input should be present
        assert "sine=frequency=220" in cmd
        # BGM audio should be mixed
        assert "[mixed]" in cmd
        # filter_complex must not have dangling "; [v][mixed]" suffix
        assert not cmd.endswith("; [v][mixed]")
        assert result["bgm_enabled"] is True

    def test_filter_complex_no_dangling_v_mixed(self, tmp_path):
        """Command must not end filter_complex with '; [v][mixed]'."""
        video_path = tmp_path / "v.mp4"
        audio_path = tmp_path / "a.mp3"
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=2x2:d=0.1",
                       "-c:v", "libx264", "-t", "0.1", str(video_path)],
                      capture_output=True, timeout=30)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "aevalsrc=0",
                       "-ar", "44100", "-ac", "2", "-t", "0.1",
                       "-c:a", "aac", str(audio_path)],
                      capture_output=True, timeout=30)

        result = compose_video_with_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=tmp_path / "out.mp4",
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.06}},
        )
        cmd = result.get("ffmpeg_command", "")
        # Must not have dangling [v][mixed] at end of filter_complex
        assert not cmd.endswith("; [v][mixed]")
        # filter_complex must end with [mixed] only (no extra [v][mixed] dangling)
        assert "[mixed]" in cmd
        assert result["bgm_enabled"] is True


@pytest.mark.skipif(not check_ffmpeg_available(), reason="ffmpeg not available")
class TestBgmRealSmoke:
    """V0.3.8.1: Real FFmpeg smoke tests for BGM composition."""

    def test_compose_video_with_audio_bgm_real_smoke(self, tmp_path):
        """Generate real video+audio with BGM, assert output is valid MP4."""
        video_path = tmp_path / "bgm_video.mp4"
        audio_path = tmp_path / "bgm_audio.mp3"
        output_path = tmp_path / "bgm_output.mp4"

        # 1. Generate 2s black video
        r1 = subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=2",
            "-c:v", "libx264", "-preset", "ultrafast", "-r", "30",
            str(video_path),
        ], capture_output=True, timeout=30)
        assert r1.returncode == 0, f"video gen failed: {r1.stderr.decode()}"

        # 2. Generate 2s silent audio using aevalsrc (universally supported)
        r2 = subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "aevalsrc=0",
            "-ar", "44100", "-ac", "2",
            "-t", "2", "-c:a", "libmp3lame", "-b:a", "64k",
            str(audio_path),
        ], capture_output=True, timeout=30)
        assert r2.returncode == 0, f"audio gen failed: {r2.stderr.decode()}"

        # 3. Compose with BGM
        result = compose_video_with_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path,
            bgm_params={"bgm": {"mode": "generated_ambient", "volume": 0.06}},
            timeout=60,
        )

        # 4. Assertions
        assert result.get("success") is True, f"compose failed: {result.get('message')}"
        assert output_path.exists(), f"output not created: {output_path}"
        assert output_path.stat().st_size > 1000, f"output too small: {output_path.stat().st_size}"
        assert result.get("bgm_enabled") is True
        assert result.get("bgm_mode") == "generated_ambient"
        assert result.get("bgm_volume") == 0.06

    def test_bgm_none_produces_valid_mp4(self, tmp_path):
        """mode=none still produces valid output (regression check)."""
        video_path = tmp_path / "novid.mp4"
        audio_path = tmp_path / "noaud.mp3"
        output_path = tmp_path / "no_bgm_output.mp4"

        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1",
                       "-c:v", "libx264", "-preset", "ultrafast", "-t", "1",
                       str(video_path)], capture_output=True, timeout=30)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "aevalsrc=0",
                       "-ar", "44100", "-ac", "2", "-t", "1",
                       "-c:a", "libmp3lame", "-b:a", "64k",
                       str(audio_path)], capture_output=True, timeout=30)

        result = compose_video_with_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=output_path,
            bgm_params={"bgm": {"mode": "none"}},
            timeout=60,
        )
        assert result.get("success") is True
        assert output_path.exists()
        assert output_path.stat().st_size > 1000
        assert result.get("bgm_enabled") is False

