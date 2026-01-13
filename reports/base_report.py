"""
PolicyHub Base Report

Base class and data structures for report generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    title: str
    subtitle: Optional[str] = None
    generated_by: str = "PolicyHub"
    include_summary: bool = True
    include_footer: bool = True
    page_size: str = "A4"  # A4 or LETTER


@dataclass
class ReportColumn:
    """Defines a column in a report table."""

    key: str
    header: str
    width: int = 100
    align: str = "left"  # left, center, right


@dataclass
class ReportData:
    """Data structure for report content."""

    config: ReportConfig
    columns: List[ReportColumn]
    rows: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)
    filters_applied: Dict[str, str] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def row_count(self) -> int:
        """Get the number of data rows."""
        return len(self.rows)


class BaseReportGenerator:
    """Base class for report generators."""

    def __init__(self, report_data: ReportData):
        """
        Initialize the report generator.

        Args:
            report_data: Report configuration and data
        """
        self.data = report_data

    def generate(self, output_path: str) -> str:
        """
        Generate the report and save to file.

        Args:
            output_path: Path to save the report

        Returns:
            Path to the generated file

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def _format_value(self, value: Any) -> str:
        """
        Format a value for display.

        Args:
            value: Value to format

        Returns:
            Formatted string
        """
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        return str(value)
