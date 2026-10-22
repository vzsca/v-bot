import panel


def test_principal_youtube_channel_count_deduplicates_across_guilds(monkeypatch):
    monkeypatch.setattr(panel.api_access, "get_allowed_guilds", lambda: {100, 200, 300})
    monkeypatch.setattr(
        panel.announcement_store,
        "load",
        lambda: {
            "announcements": [
                {"guild_id": 100, "type": "youtube", "youtube_channel_id": "UC123"},
                {"guild_id": 200, "type": "youtube", "youtube_channel_id": "UC123"},
                {"guild_id": 300, "type": "youtube", "youtube_channel_id": "UC456"},
                {
                    "guild_id": 400,
                    "type": "youtube",
                    "youtube_channel_id": "UC789",
                },
                {"guild_id": 100, "type": "twitch", "channel_id": "streamer"},
            ]
        },
    )

    assert panel._principal_youtube_channel_count() == 2


def test_cmd_start_keeps_bot_output_out_of_panel_terminal(monkeypatch, tmp_path):
    import subprocess

    main_file = tmp_path / "main.py"
    main_file.write_text("# test bot entry point", encoding="utf-8")
    python_exe = tmp_path / ("python.exe" if panel.IS_WINDOWS else "python")
    python_exe.write_text("", encoding="utf-8")
    pid_file = tmp_path / "bot.pid"
    captured = {}

    class FakeProcess:
        pid = 12345

    def fake_popen(command, **kwargs):
        captured.update(kwargs)
        return FakeProcess()

    monkeypatch.setattr(panel, "ROOT", tmp_path)
    monkeypatch.setattr(panel, "PYTHON_EXE", python_exe)
    monkeypatch.setattr(panel, "BOT_PID_FILE", pid_file)
    monkeypatch.setattr(panel, "is_running", iter([False, True]).__next__)
    monkeypatch.setattr(panel, "_write_process_metadata", lambda pid: None)
    monkeypatch.setattr(panel.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(panel.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(panel.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    assert panel.cmd_start() is True
    assert captured["stdin"] == subprocess.DEVNULL
    assert captured["stdout"] == subprocess.DEVNULL
    assert captured["stderr"] == subprocess.DEVNULL
    assert pid_file.read_text(encoding="utf-8") == "12345"
    if panel.IS_WINDOWS:
        assert captured["creationflags"] == subprocess.CREATE_NO_WINDOW
    else:
        assert captured["start_new_session"] is True
