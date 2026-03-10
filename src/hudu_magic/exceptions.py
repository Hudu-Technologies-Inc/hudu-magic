class HuduError(Exception):
    """Base exception for hudu_magic."""


class HuduConfigurationError(HuduError):
    """Raised when client or instance configuration is invalid."""


class HuduAPIError(HuduError):
    """Raised when the Hudu API returns an error response."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Hudu API error ({status_code}): {message}")