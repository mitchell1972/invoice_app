"""
PDF service for generating PDF documents.

This module defines the PDFService class which handles
generating PDF invoices and other documents.
"""
import logging
import io
from datetime import datetime
from typing import Dict, Any, Optional

# Import PDF generation library
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image, Flowable, PageBreak

from invoice_app.models.invoice import Invoice, InvoiceStatus
from invoice_app.utils.currency_utils import format_currency


logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF documents."""

    def __init__(self, config=None):
        """
        Initialize the PDF service.

        Args:
            config: Optional PDF configuration.
        """
        self.config = config or {}
        self.styles = getSampleStyleSheet()

        # Define custom styles
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for PDF documents."""
        # Heading styles
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12
        ))

        # Status style
        self.styles.add(ParagraphStyle(
            name='DraftStatus',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.red,
            alignment=1  # Center alignment
        ))

        # Header info styles
        self.styles.add(ParagraphStyle(
            name='HeaderLabel',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray
        ))

        self.styles.add(ParagraphStyle(
            name='HeaderValue',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))

        # Table header style
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold'
        ))

        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=1  # Center alignment
        ))

    def generate_invoice_pdf(self, invoice: Invoice) -> bytes:
        """
        Generate a PDF for an invoice.

        Args:
            invoice: Invoice to generate PDF for.

        Returns:
            PDF as bytes.
        """
        # Create a buffer for the PDF
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=f"Invoice {invoice.invoice_number}"
        )

        # List to hold content elements
        elements = []

        # Add invoice header
        self._add_invoice_header(elements, invoice)

        # Add customer and invoice details
        self._add_invoice_details(elements, invoice)

        # Add invoice items table
        self._add_invoice_items(elements, invoice)

        # Add totals
        self._add_invoice_totals(elements, invoice)

        # Add notes and terms
        self._add_notes_and_terms(elements, invoice)

        # Add footer
        self._add_footer(elements, invoice)

        # Build PDF
        doc.build(elements)

        # Get PDF from buffer
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _add_invoice_header(self, elements: list, invoice: Invoice) -> None:
        """
        Add invoice header to PDF elements.

        Args:
            elements: List of PDF elements to append to.
            invoice: Invoice to generate header for.
        """
        # Add title
        elements.append(Paragraph(f"INVOICE #{invoice.invoice_number}", self.styles['InvoiceTitle']))

        # Add status if draft
        if invoice.status == InvoiceStatus.DRAFT:
            elements.append(Paragraph("DRAFT - NOT FINAL", self.styles['DraftStatus']))
            elements.append(Spacer(1, 12))

        # Create a table for the header info (company and customer side by side)
        data = [
            [
                # Left column - From (Your company)
                [
                    Paragraph("FROM:", self.styles['HeaderLabel']),
                    Paragraph("Your Company Name", self.styles['HeaderValue']),
                    Paragraph("Your Address", self.styles['HeaderValue']),
                    Paragraph("Your City, State ZIP", self.styles['HeaderValue']),
                    Paragraph("Email: support@yourcompany.com", self.styles['HeaderValue']),
                    Paragraph("Phone: (123) 456-7890", self.styles['HeaderValue'])
                ],
                # Right column - To (Customer)
                [
                    Paragraph("TO:", self.styles['HeaderLabel']),
                    Paragraph(invoice.customer_name, self.styles['HeaderValue']),
                    Paragraph(f"Email: {invoice.customer_email}", self.styles['HeaderValue'])
                ]
            ]
        ]

        # Create table
        header_table = Table(data, colWidths=[doc.width/2 - 12, doc.width/2 - 12])

        # Add table to elements
        elements.append(header_table)
        elements.append(Spacer(1, 24))

    def _add_invoice_details(self, elements: list, invoice: Invoice) -> None:
        """
        Add invoice details to PDF elements.

        Args:
            elements: List of PDF elements to append to.
            invoice: Invoice to generate details for.
        """
        # Create a table for invoice details
        data = [
            [
                # Left column
                [
                    Paragraph("INVOICE DATE:", self.styles['HeaderLabel']),
                    Paragraph(invoice.issue_date.strftime("%Y-%m-%d"), self.styles['HeaderValue'])
                ],
                # Middle column
                [
                    Paragraph("DUE DATE:", self.styles['HeaderLabel']),
                    Paragraph(invoice.due_date.strftime("%Y-%m-%d"), self.styles['HeaderValue'])
                ],
                # Right column
                [
                    Paragraph("STATUS:", self.styles['HeaderLabel']),
                    Paragraph(str(invoice.status).upper(), self.styles['HeaderValue'])
                ]
            ]
        ]

        # Create table
        details_table = Table(data, colWidths=[doc.width/3 - 8, doc.width/3 - 8, doc.width/3 - 8])

        # Add table to elements
        elements.append(details_table)
        elements.append(Spacer(1, 24))

    def _add_invoice_items(self, elements: list, invoice: Invoice) -> None:
        """
        Add invoice items table to PDF elements.

        Args:
            elements: List of PDF elements to append to.
            invoice: Invoice to generate items table for.
        """
        # Create table header
        headers = [
            Paragraph("Description", self.styles['TableHeader']),
            Paragraph("Quantity", self.styles['TableHeader']),
            Paragraph("Unit Price", self.styles['TableHeader']),
            Paragraph("Total", self.styles['TableHeader'])
        ]

        # Create table data
        data = [headers]

        # Add item rows
        for item in invoice.items:
            data.append([
                Paragraph(item.description, self.styles['Normal']),
                Paragraph(f"{item.quantity:.2f}", self.styles['Normal']),
                Paragraph(format_currency(item.unit_price, invoice.currency), self.styles['Normal']),
                Paragraph(format_currency(item.total, invoice.currency), self.styles['Normal'])
            ])

        # Create table
        items_table = Table(
            data,
            colWidths=[
                doc.width * 0.5,  # Description
                doc.width * 0.15,  # Quantity
                doc.width * 0.15,  # Unit Price
                doc.width * 0.2    # Total
            ]
        )

        # Add table style
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
        ]))

        # Add table to elements
        elements.append(items_table)
        elements.append(Spacer(1, 12))

    def _add_invoice_totals(self, elements: list, invoice: Invoice) -> None:
        """
        Add invoice totals to PDF elements.

        Args:
            elements: List of PDF elements to append to.
            invoice: Invoice to generate totals for.
        """
        # Create table data for totals
        data = []

        # Add subtotal
        data.append([
            "",
            Paragraph("Subtotal:", self.styles['Normal']),
            Paragraph(format_currency(invoice.subtotal, invoice.currency), self.styles['Normal'])
        ])

        # Add discount if applicable
        if invoice.discount_percentage > 0:
            data.append([
                "",
                Paragraph(f"Discount ({invoice.discount_percentage:.2f}%):", self.styles['Normal']),
                Paragraph(f"- {format_currency(invoice.discount_amount, invoice.currency)}", self.styles['Normal'])
            ])

        # Add VAT if applicable
        if invoice.vat_rate > 0:
            data.append([
                "",
                Paragraph(f"VAT ({invoice.vat_rate:.2f}%):", self.styles['Normal']),
                Paragraph(format_currency(invoice.vat_amount, invoice.currency), self.styles['Normal'])
            ])

        # Add total
        data.append([
            "",
            Paragraph("Total:", self.styles['TableHeader']),
            Paragraph(format_currency(invoice.total, invoice.currency), self.styles['TableHeader'])
        ])

        # Create table
        totals_table = Table(
            data,
            colWidths=[
                doc.width * 0.6,  # Empty column (for alignment)
                doc.width * 0.2,  # Label
                doc.width * 0.2   # Amount
            ]
        )

        # Add table style
        totals_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('LINEABOVE', (1, -1), (2, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Add table to elements
        elements.append(totals_table)
        elements.append(Spacer(1, 24))

    def _add_notes_and_terms(self, elements: list, invoice: Invoice) -> None:
        """
        Add notes and terms to PDF elements.

        Args:
            elements: List of PDF elements to append to.
            invoice: Invoice to generate notes for.
        """
        # Add notes if available
        if invoice.notes:
            elements.append(Paragraph("Notes:", self.styles['TableHeader']))
            elements.append(Paragraph(invoice.notes, self.styles['Normal']))
            elements.append(Spacer(1, 12))

        # Add terms if available
        if invoice.terms:
            elements.append(Paragraph("Terms and Conditions:", self.styles['TableHeader']))
            elements.append(Paragraph(invoice.terms, self.styles['Normal']))
            elements.append(Spacer(1, 12))

    def _add_footer(self, elements: list, invoice: Invoice) -> None:
        """
        Add footer to PDF elements.

        Args:
            elements: List of PDF elements to append to.
            invoice: Invoice to generate footer for.
        """
        # Add thank you note
        elements.append(Paragraph("Thank you for your business!", self.styles['Footer']))

        # Add payment instructions
        payment_text = f"""
        Please make payment by the due date ({invoice.due_date.strftime('%Y-%m-%d')}).
        """
        elements.append(Paragraph(payment_text, self.styles['Footer']))

        # Add generator note
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Footer']
        ))