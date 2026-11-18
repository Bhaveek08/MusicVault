from pathlib import Path
import pytest

from musicvault_core import (
    APP_NAME, APP_VERSION, SourceValidationError, UnsupportedServiceError,
    build_ydl_options, format_bytes, format_eta, get_app_data_dir,
    validate_output_folder, validate_source_url, validate_spotify_url,
)


@pytest.mark.parametrize("url,source_id", [
    ("https://www.youtube.com/watch?v=BaW_jenozKc", "BaW_jenozKc"),
    ("https://youtu.be/BaW_jenozKc", "BaW_jenozKc"),
    ("https://www.youtube.com/shorts/BaW_jenozKc", "BaW_jenozKc"),
])
def test_valid_youtube_urls(url, source_id):
    assert validate_source_url(url).source_id == source_id


def test_playlist_only_url():
    source = validate_source_url("https://www.youtube.com/playlist?list=PL1234567890")
    assert source.is_playlist_only


@pytest.mark.parametrize("url", [
    "http://www.youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com.evil.example/watch?v=BaW_jenozKc",
    "https://evil.example/watch?v=BaW_jenozKc",
    "https://user:pass@youtube.com/watch?v=BaW_jenozKc",
    "https://youtube.com:444/watch?v=BaW_jenozKc",
    "javascript:alert(1)",
    "",
    "x" * 3000,
])
def test_rejects_unsafe_youtube_urls(url):
    with pytest.raises(SourceValidationError):
        validate_source_url(url)


def test_spotify_is_not_a_download_source():
    with pytest.raises(UnsupportedServiceError):
        validate_source_url("https://open.spotify.com/track/1234567890123456789012")


@pytest.mark.parametrize("url", [
    "https://open.spotify.com/track/1234567890123456789012",
    "https://open.spotify.com/album/1234567890123456789012",
    "https://open.spotify.com/playlist/1234567890123456789012",
    "https://spotify.link/AbCdEf",
])
def test_valid_spotify_handoff_links(url):
    assert validate_spotify_url(url).startswith("https://")


@pytest.mark.parametrize("url", [
    "http://open.spotify.com/track/1234567890123456789012",
    "https://spotify.com.evil.example/track/1234567890123456789012",
    "https://evil.example/track/1234567890123456789012",
    "https://user:pass@open.spotify.com/track/1234567890123456789012",
])
def test_rejects_unsafe_spotify_links(url):
    with pytest.raises(SourceValidationError):
        validate_spotify_url(url)


def test_app_data_dir_is_per_user(tmp_path):
    path = get_app_data_dir(platform="win32", env={"LOCALAPPDATA": str(tmp_path)}, home=str(tmp_path))
    assert path == tmp_path
    path = get_app_data_dir(platform="darwin", env={}, home=str(tmp_path))
    assert path == tmp_path / "Library" / "Application Support"


def test_output_folder_creates_and_writes(tmp_path):
    out = validate_output_folder(tmp_path / "downloads")
    assert out.is_dir()
    assert list(out.iterdir()) == []


@pytest.mark.parametrize("fmt", ["MP3", "WAV", "FLAC", "M4A", "AAC", "OPUS", "MKV"])
def test_supported_output_formats_are_mapped(fmt, tmp_path):
    src = validate_source_url("https://youtu.be/BaW_jenozKc")
    opts = build_ydl_options(
        url=src.url, output_dir=tmp_path, output_format=fmt,
        include_playlist=False, ffmpeg_location=None,
        progress_hook=lambda data: None, logger=None, deno_path=None,
    )
    assert "outtmpl" in opts
    assert opts["noplaylist"] is True
    assert "cookiefile" not in opts
    assert opts.get("remote_components") == []


def test_audio_targets_high_quality_when_lossy(tmp_path):
    src = validate_source_url("https://youtu.be/BaW_jenozKc")
    opts = build_ydl_options(
        url=src.url, output_dir=tmp_path, output_format="MP3",
        include_playlist=False, ffmpeg_location=None,
        progress_hook=lambda data: None, logger=None, deno_path=None,
    )
    assert opts["postprocessors"][0]["preferredquality"] == "320"


def test_format_helpers_handle_invalid_values():
    assert format_bytes(float("nan")) == ""
    assert format_eta(float("inf")) == ""


def test_version_identity():
    assert APP_NAME == "MusicVault"
    assert APP_VERSION == "2.0.0"
