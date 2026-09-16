"""Configuration validation tests."""

import pytest

from grist.grist import GristClient
from utils import require_grist_profile


def test_require_grist_profile_returns_explicit_normalized_connection():
    profile = require_grist_profile(
        {
            "ad_tracking": {
                "doc_id": " doc-123 ",
                "api_key": " key-456 ",
                "server": " https://team.getgrist.com/ ",
                "ads_table_id": "Ads",
            }
        },
        "ad_tracking",
    )

    assert profile == {
        "doc_id": "doc-123",
        "api_key": "key-456",
        "server": "https://team.getgrist.com",
        "ads_table_id": "Ads",
    }


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"ad_tracking": None},
        {"ad_tracking": {}},
        {"ad_tracking": {"doc_id": "doc", "api_key": "key"}},
        {
            "ad_tracking": {
                "doc_id": "doc",
                "api_key": "key",
                "server": "   ",
            }
        },
    ],
)
def test_require_grist_profile_rejects_incomplete_connections(config):
    with pytest.raises(ValueError, match="Grist profile 'ad_tracking'"):
        require_grist_profile(config, "ad_tracking")


def test_grist_client_requires_an_explicit_server():
    with pytest.raises(TypeError):
        GristClient("doc", "key")

    with pytest.raises(ValueError, match="configured explicitly"):
        GristClient("doc", "key", "   ")


@pytest.mark.parametrize("server", ["/", "docs.getgrist.com", "ftp://example.com"])
def test_grist_servers_must_be_absolute_http_urls(server):
    config = {
        "ad_tracking": {
            "doc_id": "doc",
            "api_key": "key",
            "server": server,
        }
    }

    with pytest.raises(ValueError, match=r"absolute HTTP\(S\) URL"):
        require_grist_profile(config, "ad_tracking")

    with pytest.raises(ValueError, match=r"absolute HTTP\(S\) URL"):
        GristClient("doc", "key", server)
