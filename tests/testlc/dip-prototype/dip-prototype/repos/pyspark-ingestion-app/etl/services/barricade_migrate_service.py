"""BarricadeMigrateService - SERVICE (not a skill).

Handles barricade encryption/decryption migration patterns (KMS key refs
from config, never hardcoded - Barricade B1).
"""


class BarricadeMigrateService:
    def migrate(self, config):
        raise NotImplementedError("prototype stub")
