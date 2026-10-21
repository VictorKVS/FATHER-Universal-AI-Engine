"""Gitea provider adapter."""

from providers.gitea_compatible_adapter import GiteaCompatibleAdapter


class GiteaAdapter(GiteaCompatibleAdapter):
    provider_id = "gitea"
    env_prefix = "FATHER_GITEA"
    default_base_url = "https://gitea.com"
