"""
Custom application exceptions for clear, structured error handling.
"""


class MissingDateColumnError(ValueError):
    """Raised when the expected 'Date' column is not found in the uploaded file."""
    def __init__(self, column_name: str, available_columns: list[str]):
        self.column_name = column_name
        self.available_columns = available_columns
        super().__init__(
            f"Column '{column_name}' not found. "
            f"Available columns: {available_columns}"
        )


class EmptyDateRangeError(ValueError):
    """Raised when no rows match the provided date range filter."""
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        super().__init__(
            f"No data found between '{start_date}' and '{end_date}'. "
            "Please verify the date range."
        )


class InvalidFileFormatError(ValueError):
    """Raised when the uploaded file cannot be parsed as a valid Excel file."""
    def __init__(self, detail: str = ""):
        super().__init__(
            f"Invalid or corrupted Excel file. Only .xlsx files are supported. "
            f"Detail: {detail}"
        )


class AIServiceError(RuntimeError):
    """Raised when the AI generative model call fails."""
    def __init__(self, detail: str = ""):
        super().__init__(f"AI service error: {detail}")
