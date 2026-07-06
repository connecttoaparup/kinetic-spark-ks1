"""TsqlToBqService - SERVICE (not a skill).

Converts MS SQL Server (T-SQL) queries to BigQuery SQL.
"""


class TsqlToBqService:
    def convert(self, tsql: str) -> str:
        raise NotImplementedError("prototype stub")
