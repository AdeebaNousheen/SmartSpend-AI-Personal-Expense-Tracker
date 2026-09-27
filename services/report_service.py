"""
SmartSpend - Report Service
Exports financial data to CSV and compiles styled PDF summary reports using ReportLab.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import config
from database.db_manager import DatabaseManager
from services.expense_service import ExpenseService
from services.settings_service import SettingsService


class ReportService:
    """Generates analytical reports and file exports."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.expense_service = ExpenseService(self.db)
        self.settings_service = SettingsService(self.db)

    def export_csv(
        self,
        output_filepath: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> str:
        """
        Exports filtered expense transactions to a structured CSV file.
        """
        expenses = self.expense_service.get_expenses(
            start_date=start_date,
            end_date=end_date,
            category=category,
            is_demo=is_demo,
            sort_by="date",
            sort_order="DESC"
        )

        output_filepath = Path(output_filepath)
        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "ID", "Date", "Title", "Category", "Amount",
            "Payment_Method", "Notes", "Is_Anomaly", "Anomaly_Reason", "Is_Demo"
        ]

        with open(output_filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for exp in expenses:
                writer.writerow({
                    "ID": exp["id"],
                    "Date": exp["date"],
                    "Title": exp["title"],
                    "Category": exp["category"],
                    "Amount": f"{exp['amount']:.2f}",
                    "Payment_Method": exp["payment_method"],
                    "Notes": exp["notes"] or "",
                    "Is_Anomaly": "Yes" if exp["is_anomaly"] else "No",
                    "Anomaly_Reason": exp["anomaly_reason"] or "",
                    "Is_Demo": "Demo" if exp["is_demo"] else "User",
                })

        return str(output_filepath)

    def generate_summary_text(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> str:
        """Generates a plain-text markdown financial summary."""
        total = self.expense_service.get_total_spent(start_date, end_date, is_demo)
        by_cat = self.expense_service.get_spending_by_category(start_date, end_date, is_demo)
        anomalies = self.expense_service.get_expenses(start_date=start_date, end_date=end_date, is_anomaly=1, is_demo=is_demo)
        sym = self.settings_service.get_currency_symbol()

        lines = [
            "=" * 50,
            f"          {config.APP_NAME} - Financial Summary Report",
            "=" * 50,
            f"Period: {start_date or 'Beginning'} to {end_date or 'Present'}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Currency: {self.settings_service.get_currency_code()} ({sym})",
            "-" * 50,
            f"TOTAL SPENT: {self.settings_service.format_currency(total)}",
            "-" * 50,
            "\nCATEGORY BREAKDOWN:",
        ]

        for item in by_cat:
            cat_total = item["total_amount"]
            pct = (cat_total / total * 100.0) if total > 0 else 0.0
            lines.append(f"  • {item['category']:<22}: {self.settings_service.format_currency(cat_total):>12} ({pct:.1f}%) [{item['tx_count']} txs]")

        if anomalies:
            lines.append("\n" + "-" * 50)
            lines.append("FLAGGED UNUSUAL TRANSACTIONS (ANOMALIES):")
            for a in anomalies:
                lines.append(f"  [!] {a['date']} - {a['title']} - {self.settings_service.format_currency(a['amount'])}")
                if a["anomaly_reason"]:
                    lines.append(f"      Reason: {a['anomaly_reason']}")

        lines.append("=" * 50)
        return "\n".join(lines)

    def export_pdf(
        self,
        output_filepath: Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_demo: Optional[int] = None,
    ) -> str:
        """
        Compiles a professional PDF statement using ReportLab.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        output_filepath = Path(output_filepath)
        output_filepath.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_filepath),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=14
        )
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#2563EB'),
            spaceBefore=12,
            spaceAfter=8
        )
        body_style = styles['Normal']

        story = []

        # 1. Header
        story.append(Paragraph(f"<b>{config.APP_NAME}</b> - Financial Expense Report", title_style))
        period_str = f"Period: {start_date or 'Inception'} to {end_date or 'Present'} | Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        story.append(Paragraph(period_str, subtitle_style))
        story.append(Spacer(1, 10))

        # 2. Executive Metrics Summary
        total = self.expense_service.get_total_spent(start_date, end_date, is_demo)
        by_cat = self.expense_service.get_spending_by_category(start_date, end_date, is_demo)
        tx_count = sum(c["tx_count"] for c in by_cat)
        curr_code = self.settings_service.get_currency_code()

        summary_data = [
            ["Metric", "Value"],
            ["Total Expenditure", f"{curr_code} {total:,.2f}"],
            ["Total Transactions", str(tx_count)],
            ["Active Categories", str(len(by_cat))],
            ["Average Per Transaction", f"{curr_code} {(total / tx_count):,.2f}" if tx_count > 0 else f"{curr_code} 0.00"],
        ]
        summary_table = Table(summary_data, colWidths=[200, 300])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # 3. Category Breakdown Table
        story.append(Paragraph("Category Spending Distribution", section_style))
        cat_table_data = [["Category", f"Amount ({curr_code})", "% of Total", "Transactions"]]
        for item in by_cat:
            c_amt = item["total_amount"]
            c_pct = (c_amt / total * 100.0) if total > 0 else 0.0
            cat_table_data.append([
                item["category"],
                f"{c_amt:,.2f}",
                f"{c_pct:.1f}%",
                str(item["tx_count"])
            ])

        if len(cat_table_data) > 1:
            cat_table = Table(cat_table_data, colWidths=[180, 130, 100, 90])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
            ]))
            story.append(cat_table)
        else:
            story.append(Paragraph("No expenses found for this time range.", body_style))

        # 4. Anomalies Section
        anomalies = self.expense_service.get_expenses(start_date=start_date, end_date=end_date, is_anomaly=1, is_demo=is_demo)
        if anomalies:
            story.append(Spacer(1, 15))
            story.append(Paragraph("Flagged Unusual Spending (Anomalies)", section_style))
            anom_data = [["Date", "Title", "Category", f"Amount ({curr_code})", "AI Explanation"]]
            for a in anomalies[:10]:  # Cap at top 10 for neat PDF page
                anom_data.append([
                    a["date"],
                    Paragraph(a["title"], body_style),
                    a["category"],
                    f"{a['amount']:,.2f}",
                    Paragraph(a["anomaly_reason"] or "Flagged by ML isolation model", body_style)
                ])
            anom_table = Table(anom_data, colWidths=[70, 110, 90, 80, 150])
            anom_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF4444')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FECACA')),
            ]))
            story.append(anom_table)

        doc.build(story)
        return str(output_filepath)
