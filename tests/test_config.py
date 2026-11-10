from app.core.config import Settings


def test_cors_origins_are_split_and_trimmed():
    config = Settings(cors_origins="http://localhost:5173, https://example.com")

    assert config.cors_origin_list == ["http://localhost:5173", "https://example.com"]
