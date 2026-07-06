"""RESTService - generic REST ingestion service (prototype stub)."""


class RESTService:
    """Reads paginated REST APIs into DataFrames. url_token pagination
    supports differing response-field / query-param names via
    url_token_param_tag (see CHANGELOG 1.2.1)."""

    def read(self, config):  # -> DataFrame
        raise NotImplementedError("prototype stub")
