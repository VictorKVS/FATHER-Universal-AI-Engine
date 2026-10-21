"""Forgejo provider adapter."""

from providers.gitea_compatible_adapter import GiteaCompatibleAdapter


class ForgejoAdapter(GiteaCompatibleAdapter):
    provider_id = "forgejo"
    env_prefix = "FATHER_FORGEJO"
    default_base_url = "https://code.forgejo.org"
