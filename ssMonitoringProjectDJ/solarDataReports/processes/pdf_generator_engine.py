"""
PDF Generator Engine for Solar Data Reports
Handles conversion of text reports into PDF format
"""

import logging
import tempfile
import os
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
except ImportError:
    # Handle case where reportlab is not installed
    pass

# Initialize logger
logger = logging.getLogger('solarDataReports.pdf_generator')

class SolarDataPDFGenerator:
    """
    Handles conversion of analysis reports into PDF format
    """
    
    def __init__(self):
        """Initialize PDF generator with default settings"""
        self.page_size = A4
        self.margin = 0.75 * inch
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF"""
        # Main title style
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor='#2c3e50'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor='#34495e'
        ))
        
        # Report content style
        self.styles.add(ParagraphStyle(
            name='ReportContent',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=3,
            spaceAfter=3,
            leftIndent=10
        ))
        
        # Header line style
        self.styles.add(ParagraphStyle(
            name='HeaderLine',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceBefore=5,
            spaceAfter=5,
            alignment=TA_CENTER,
            textColor='#7f8c8d'
        ))
    
    def simple_report(self, report_texts, title="Solar Production Analysis Report", date=None):
        """
        Generate a simple PDF report by combining multiple text reports
        
        Args:
            report_texts (list): List of text reports to include in PDF
            title (str): Main title for the PDF report
            date (str): Date for the report (defaults to today)
            
        Returns:
            str: Path to the generated PDF file
        """
        logger.info(f"Generating simple PDF report with {len(report_texts)} sections")
        
        try:
            # Validate reportlab is available
            if 'SimpleDocTemplate' not in globals():
                raise ImportError("reportlab library is required for PDF generation")
            
            # Use provided date or default to today
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Create temporary file for PDF
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.pdf', 
                prefix=f'solar_report_{date}_'
            )
            temp_file.close()
            
            logger.debug(f"Creating PDF at: {temp_file.name}")
            
            # Create PDF document
            doc = SimpleDocTemplate(
                temp_file.name,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Build PDF content
            story = []
            
            # Add main title
            story.append(Paragraph(title, self.styles['MainTitle']))
            story.append(Spacer(1, 12))
            
            # Add date and generation info
            generation_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(generation_info, self.styles['HeaderLine']))
            story.append(Spacer(1, 20))
            
            # Process each text report
            for i, report_text in enumerate(report_texts):
                logger.debug(f"Processing report section {i+1}/{len(report_texts)}")
                
                if not report_text or not report_text.strip():
                    logger.warning(f"Skipping empty report section {i+1}")
                    continue
                
                # Split report into lines and process
                lines = report_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    
                    if not line:
                        # Empty line - add small spacer
                        story.append(Spacer(1, 6))
                        continue
                    
                    # Detect different line types and apply appropriate styling
                    if line.startswith('=') and line.endswith('='):
                        # Header separator line - skip, we handle headers differently
                        continue
                    elif any(header in line.upper() for header in ['REPORT', 'ANALYSIS']):
                        # Main section headers
                        story.append(Paragraph(line, self.styles['SectionHeader']))
                    elif line.startswith('EXECUTIVE SUMMARY:') or line.startswith('DETAILED FINDINGS:') or line.startswith('RECOMMENDED ACTIONS:'):
                        # Subsection headers
                        story.append(Spacer(1, 10))
                        story.append(Paragraph(f"<b>{line}</b>", self.styles['Normal']))
                    elif line.startswith('Analysis Date:'):
                        # Date line
                        story.append(Paragraph(line, self.styles['HeaderLine']))
                    elif line.startswith('-') and len(set(line)) == 1:
                        # Separator lines - convert to spacer
                        story.append(Spacer(1, 8))
                    else:
                        # Regular content
                        # Escape HTML characters and preserve formatting
                        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(escaped_line, self.styles['ReportContent']))
                
                # Add page break between major sections (except for zero production sections)
                if i < len(report_texts) - 1:
                    # Don't add page break between zero production sections
                    next_text = report_texts[i + 1]
                    if not (("ZERO PRODUCTION ANALYSIS" in report_text and "ZERO PRODUCTION ANALYSIS" in next_text) or
                           (i == 0 and "ANALYSIS SUMMARY" in report_text)):  # Don't break after summary
                        story.append(PageBreak())
            
            # Build the PDF
            doc.build(story)
            
            # Verify file was created and has content
            if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                file_size = os.path.getsize(temp_file.name)
                logger.info(f"PDF generated successfully: {temp_file.name} ({file_size} bytes)")
                return temp_file.name
            else:
                logger.error("PDF file was not created or is empty")
                return None
                
        except ImportError as e:
            logger.error(f"Missing required library for PDF generation: {str(e)}")
            logger.error("Please install reportlab: pip install reportlab")
            return None
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            return None
    
    def cleanup_temp_file(self, file_path):
        """
        Safely delete temporary PDF file
        
        Args:
            file_path (str): Path to the PDF file to delete
            
        Returns:
            bool: True if file was deleted successfully, False otherwise
        """
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary PDF file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to cleanup PDF file {file_path}: {str(e)}")
            return False
    
    def generate_in_memory(self, report_texts, title="Solar Production Analysis Report", date=None):
        """
        Generate PDF in memory without creating temporary files
        
        Args:
            report_texts (list): List of text reports to include in PDF
            title (str): Main title for the PDF report
            date (str): Date for the report
            
        Returns:
            BytesIO: PDF content as bytes, or None if generation failed
        """
        logger.info(f"Generating in-memory PDF report with {len(report_texts)} sections")
        
        try:
            # Validate reportlab is available
            if 'SimpleDocTemplate' not in globals():
                raise ImportError("reportlab library is required for PDF generation")
            
            # Use provided date or default to today
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Create in-memory buffer
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Build PDF content (reuse logic from simple_report)
            story = []
            
            # Add main title
            story.append(Paragraph(title, self.styles['MainTitle']))
            story.append(Spacer(1, 12))
            
            # Add date and generation info
            generation_info = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            story.append(Paragraph(generation_info, self.styles['HeaderLine']))
            story.append(Spacer(1, 20))
            
            # Process each text report (same logic as simple_report)
            for i, report_text in enumerate(report_texts):
                if not report_text or not report_text.strip():
                    continue
                
                lines = report_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        story.append(Spacer(1, 6))
                        continue
                    
                    if line.startswith('=') and line.endswith('='):
                        continue
                    elif any(header in line.upper() for header in ['REPORT', 'ANALYSIS']):
                        story.append(Paragraph(line, self.styles['SectionHeader']))
                    elif line.startswith('EXECUTIVE SUMMARY:') or line.startswith('DETAILED FINDINGS:') or line.startswith('RECOMMENDED ACTIONS:'):
                        story.append(Spacer(1, 10))
                        story.append(Paragraph(f"<b>{line}</b>", self.styles['Normal']))
                    elif line.startswith('Analysis Date:'):
                        story.append(Paragraph(line, self.styles['HeaderLine']))
                    elif line.startswith('-') and len(set(line)) == 1:
                        story.append(Spacer(1, 8))
                    else:
                        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(escaped_line, self.styles['ReportContent']))
                
                if i < len(report_texts) - 1:
                    # Don't add page break between zero production sections
                    next_text = report_texts[i + 1]
                    if not (("ZERO PRODUCTION ANALYSIS" in report_text and "ZERO PRODUCTION ANALYSIS" in next_text) or
                           (i == 0 and "ANALYSIS SUMMARY" in report_text)):  # Don't break after summary
                        story.append(PageBreak())
            
            # Build the PDF
            doc.build(story)
            
            # Get PDF content
            buffer.seek(0)
            logger.info(f"In-memory PDF generated successfully ({len(buffer.getvalue())} bytes)")
            return buffer
            
        except ImportError as e:
            logger.error(f"Missing required library for PDF generation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error generating in-memory PDF: {str(e)}")
            return None
