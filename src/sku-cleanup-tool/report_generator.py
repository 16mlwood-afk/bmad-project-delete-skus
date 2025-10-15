"""
Report generation for SKU Cleanup Tool
Creates markdown reports with cleanup results and statistics
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates cleanup reports and manages report files"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive cleanup report"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"sku-cleanup-report-{timestamp}.md"
        filepath = self.output_dir / filename

        # Generate report content
        report_content = self._build_report_content(results)

        # Write report file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)

        logger.info(f"Report saved to: {filepath}")
        return str(filepath)

    def _build_report_content(self, results: Dict[str, Any]) -> str:
        """Build the complete report content"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""# SKU Cleanup Report
**Date:** {timestamp}
    **Execution Time:** {results.get('execution_time', 0):.2f} seconds

## Summary
- **Total SKUs Processed:** {results.get('total_processed', 0)}
- **Eligible for Deletion:** {results.get('eligible_for_deletion', 0)}
- **Successfully Deleted:** {len(results.get('deleted', []))}
- **Skipped:** {len(results.get('skipped', []))}
- **Errors:** {len(results.get('errors', []))}

## Deleted SKUs ({len(results.get('deleted', []))})

"""

        if results.get('deleted'):
            report += "| SKU | Status |\n"
            report += "|-----|--------|\n"

            for sku in results.get('deleted', []):
                report += f"| {sku} | ✅ Deleted |\n"
        else:
            report += "_No SKUs were deleted in this run._\n"

        report += f"\n## Skipped SKUs ({len(results.get('skipped', []))})\n\n"

        if results.get('skipped'):
            # Group by reason
            skip_reasons = {}
            for skip in results.get('skipped', []):
                reason = skip.get('reason', 'unknown')
                if reason not in skip_reasons:
                    skip_reasons[reason] = []
                skip_reasons[reason].append(skip.get('sku', 'unknown'))

            for reason, skus in skip_reasons.items():
                report += f"### {reason.replace('_', ' ').title()} ({len(skus)})\n"
                for sku in skus:
                    report += f"- {sku}\n"
                report += "\n"
        else:
            report += "_No SKUs were skipped in this run._\n"

        # Error section
        if results.get('errors'):
            report += f"## Errors ({len(results.get('errors', []))})\n\n"
            for error in results.get('errors', []):
                sku = error.get('sku', 'unknown')
                error_msg = error.get('error', 'unknown error')
                report += f"- **{sku}**: {error_msg}\n"
        else:
            report += "\n## Errors\n_No errors occurred during this run._\n"

        # Performance metrics
        report += "\n## Performance Metrics\n\n"
        report += f"- **Execution Time:** {results.get('execution_time', 0):.2f} seconds\n"
        report += f"- **SKUs Processed per Second:** {results.get('total_processed', 0) / max(results.get('execution_time', 1), 1):.2f}\n"

        if results.get('total_processed', 0) > 0:
            success_rate = len(results.get('deleted', [])) / results.get('total_processed', 1) * 100
            report += f"- **Success Rate:** {success_rate:.1f}%\n"

        # Recommendations
        report += "\n## Recommendations\n\n"

        if results.get('eligible_for_deletion', 0) == 0:
            report += "- ✅ **Catalog is clean** - No old SKUs found for deletion\n"
        elif len(results.get('deleted', [])) == results.get('eligible_for_deletion', 0):
            report += "- ✅ **Cleanup successful** - All eligible SKUs were deleted\n"
        else:
            report += "- ⚠️  **Review skipped SKUs** - Some eligible SKUs were not deleted\n"

        if results.get('errors'):
            report += "- 🔧 **Check logs** - Errors occurred during execution\n"

        report += "- 📅 **Schedule daily** - Run this tool daily for ongoing maintenance\n"

        return report

    def generate_summary_report(self, daily_reports: List[str]) -> str:
        """Generate a summary report from multiple daily reports"""
        # This could aggregate data from multiple report files
        # For now, just return a placeholder
        return "# Weekly/Monthly Summary Report\n\nFeature coming soon..."

    def cleanup_old_reports(self, keep_days: int = 30):
        """Clean up old report files"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)

        if not self.output_dir.exists():
            return

        cleaned_count = 0
        for report_file in self.output_dir.glob("sku-cleanup-report-*.md"):
            try:
                # Extract timestamp from filename (sku-cleanup-report-YYYY-MM-DD_HH-MM-SS.md)
                filename = report_file.name
                if filename.startswith("sku-cleanup-report-") and filename.endswith(".md"):
                    date_str = filename[19:-3]  # Remove "sku-cleanup-report-" (19 chars) and ".md" (3 chars)
                    if '_' in date_str:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                    else:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        report_file.unlink()
                        cleaned_count += 1

            except (ValueError, OSError) as e:
                logger.warning(f"Could not process report file {report_file}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old report files")

    def list_reports(self) -> List[Dict[str, Any]]:
        """List all available reports with metadata"""
        reports = []

        if not self.output_dir.exists():
            return reports

        for report_file in sorted(self.output_dir.glob("sku-cleanup-report-*.md")):
            try:
                # Extract timestamp from filename
                timestamp_str = report_file.stem.replace("sku-cleanup-report-", "")
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")

                # Get file size
                size = report_file.stat().st_size

                reports.append({
                    'filename': report_file.name,
                    'timestamp': timestamp,
                    'size': size,
                    'path': str(report_file)
                })

            except (ValueError, OSError) as e:
                logger.warning(f"Could not process report file {report_file}: {e}")

        return reports
