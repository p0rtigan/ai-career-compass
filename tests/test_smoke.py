from pathlib import Path


def test_readme_exists():
    assert Path("README.md").is_file()


def test_app_entrypoint_exists():
    assert Path("app/match_explorer.py").is_file()
