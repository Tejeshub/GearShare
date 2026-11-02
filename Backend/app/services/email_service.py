import email.utils
import logging
import smtplib
from datetime import datetime, timezone
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_enquiry_confirmation_email(
        recipient_email: str,
        customer_name: str,
        reference_id: str,
        start_date: str,
        end_date: str,
        duration_days: int,
        formatted_total: str,
        hold_expires_at_iso: str,
        quote_lines: List[Dict[str, Any]],
        kit_title: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Sends transactional confirmation email to customer via standard SMTP (Gmail).
        Returns (True, None) if accepted by SMTP server, (False, error_reason) otherwise.
        Never raises uncaught exceptions to ensure enquiry creation is never aborted.
        """
        settings = get_settings()

        if not settings.EMAIL_ENABLED:
            logger.info(
                "Email notifications are disabled (EMAIL_ENABLED=false). Skipping email for %s.",
                reference_id,
            )
            return False, "Email notifications are disabled (EMAIL_ENABLED=false)"

        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            logger.warning(
                "SMTP host/port is not configured. Skipping confirmation email for %s.",
                reference_id,
            )
            return False, "SMTP server not configured"

        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD or not settings.SMTP_PASSWORD.get_secret_value():
            logger.warning(
                "SMTP credentials are not configured. Skipping confirmation email for %s.",
                reference_id,
            )
            return False, "SMTP credentials not configured"

        # Format hold expiry for human display
        try:
            hold_dt = datetime.fromisoformat(hold_expires_at_iso.replace("Z", "+00:00"))
            hold_display = hold_dt.strftime("%d %b %Y, %I:%M %p UTC")
        except Exception:
            hold_display = hold_expires_at_iso

        # Build items table HTML
        items_rows_html = ""
        items_text_lines = []
        for line in quote_lines:
            name = line.get("name", "Equipment")
            qty = line.get("quantity", 1)
            line_type = line.get("type", "product")
            brand = line.get("brand") or ""
            subtotal = line.get("subtotal", 0)
            formatted_subtotal = f"₹{Decimal(str(subtotal)):,.2f}"

            badge = "CREATOR KIT" if line_type == "kit" else "EQUIPMENT"
            brand_display = f" &bull; {brand}" if brand else ""

            items_rows_html += f"""
            <tr>
              <td style="padding: 12px 0; border-bottom: 1px solid #222428; color: #f4f4f2; font-size: 13px;">
                <div style="font-weight: 600;">{name}</div>
                <div style="font-size: 11px; color: #8c9094; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px;">
                  {badge}{brand_display}
                </div>
              </td>
              <td style="padding: 12px 0; border-bottom: 1px solid #222428; color: #c5c8cb; font-size: 13px; text-align: center;">
                {qty}
              </td>
              <td style="padding: 12px 0; border-bottom: 1px solid #222428; color: #f4f4f2; font-size: 13px; text-align: right; font-family: monospace;">
                {formatted_subtotal}
              </td>
            </tr>
            """
            items_text_lines.append(f"- {qty}x {name} ({formatted_subtotal})")

        items_text_summary = "\n".join(items_text_lines)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Rental Enquiry Received — GearShare</title>
</head>
<body style="margin: 0; padding: 0; background-color: #060708; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f4f4f2;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #060708; padding: 40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #0c0d0e; border: 1px solid #222428; border-radius: 4px; overflow: hidden; text-align: left;">
          <!-- Header Branding -->
          <tr>
            <td style="padding: 32px 36px; background-color: #0c0d0e; border-bottom: 1px solid #222428;">
              <table width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <span style="font-size: 18px; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #ffffff;">GEARSHARE</span>
                    <span style="display: block; font-size: 10px; color: #717478; letter-spacing: 0.18em; text-transform: uppercase; margin-top: 4px;">Cinematography & Creative Rentals</span>
                  </td>
                  <td align="right">
                    <span style="display: inline-block; background-color: #17191c; border: 1px solid #2d3035; color: #e2e8f0; font-family: monospace; font-size: 11px; padding: 6px 12px; border-radius: 2px; letter-spacing: 0.08em;">
                      {reference_id}
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Message -->
          <tr>
            <td style="padding: 36px 36px 24px 36px;">
              <h1 style="margin: 0 0 12px 0; font-size: 22px; font-weight: 600; color: #ffffff; letter-spacing: -0.02em;">
                We have received your enquiry, {customer_name}.
              </h1>
              <p style="margin: 0 0 20px 0; font-size: 14px; line-height: 1.6; color: #a1a5a9;">
                Your rental enquiry has been received and logged in our reservation system. The equipment has been placed under a 
                <strong style="color: #ffffff;">24-hour temporary inventory hold</strong> while our rental coordinators review your shoot requirements and confirm equipment dispatch.
              </p>

              <!-- Hold Notice Box -->
              <div style="background-color: #121417; border-left: 3px solid #ffffff; padding: 14px 18px; margin-bottom: 28px;">
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em; color: #8c9094; font-weight: 600;">24-Hour Hold Expiry</div>
                <div style="font-size: 13px; color: #ffffff; font-family: monospace; margin-top: 4px;">{hold_display}</div>
              </div>

              <!-- Rental Details Overview -->
              <table width="100%" cellspacing="0" cellpadding="0" style="background-color: #060708; border: 1px solid #1c1e22; margin-bottom: 28px;">
                <tr>
                  <td style="padding: 14px 16px; border-right: 1px solid #1c1e22; width: 33%;">
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.14em; color: #717478;">Start Date</div>
                    <div style="font-size: 13px; color: #ffffff; font-weight: 500; margin-top: 4px;">{start_date}</div>
                  </td>
                  <td style="padding: 14px 16px; border-right: 1px solid #1c1e22; width: 33%;">
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.14em; color: #717478;">End Date</div>
                    <div style="font-size: 13px; color: #ffffff; font-weight: 500; margin-top: 4px;">{end_date}</div>
                  </td>
                  <td style="padding: 14px 16px; width: 34%;">
                    <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.14em; color: #717478;">Duration</div>
                    <div style="font-size: 13px; color: #ffffff; font-weight: 500; margin-top: 4px;">{duration_days} Calendar Days</div>
                  </td>
                </tr>
              </table>

              <!-- Itemized Breakdown -->
              <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.16em; color: #717478; font-weight: 600; margin-bottom: 12px;">
                Requested Equipment Breakdown
              </div>
              <table width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px;">
                <thead>
                  <tr style="border-bottom: 1px solid #222428;">
                    <th style="padding: 8px 0; text-align: left; font-size: 11px; color: #717478; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500;">Item</th>
                    <th style="padding: 8px 0; text-align: center; font-size: 11px; color: #717478; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500; width: 60px;">Qty</th>
                    <th style="padding: 8px 0; text-align: right; font-size: 11px; color: #717478; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500; width: 100px;">Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {items_rows_html}
                </tbody>
              </table>

              <!-- Total Quote Summary -->
              <table width="100%" cellspacing="0" cellpadding="0" style="border-top: 1px solid #2d3035; padding-top: 14px; margin-bottom: 32px;">
                <tr>
                  <td style="font-size: 14px; font-weight: 600; color: #ffffff; text-transform: uppercase; letter-spacing: 0.08em;">
                    Estimated Rental Total
                  </td>
                  <td align="right" style="font-size: 20px; font-weight: 700; color: #ffffff; font-family: monospace;">
                    {formatted_total}
                  </td>
                </tr>
              </table>

              <!-- Next Steps Notice -->
              <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #a1a5a9;">
                Our team will reach out via WhatsApp or phone within a few hours to confirm equipment dispatch, ID verification, and security deposit details.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 36px; background-color: #060708; border-top: 1px solid #222428; text-align: center; font-size: 11px; color: #63676b; line-height: 1.6;">
              &copy; {datetime.now(timezone.utc).year} GearShare Cinematography & Equipment Rentals.<br>
              Reference {reference_id} &bull; Keep this email for your records.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        plain_text = f"""GearShare — Rental Enquiry Received
==================================================

Hello {customer_name},

Thank you for your rental enquiry. We have received your request and placed the requested gear on a temporary 24-hour hold awaiting team confirmation.

ENQUIRY REFERENCE: {reference_id}
RENTAL DURATION: {start_date} to {end_date} ({duration_days} calendar days)
HOLD EXPIRES AT: {hold_display}

REQUESTED EQUIPMENT:
{items_text_summary}

ESTIMATED TOTAL: {formatted_total}

Our team will contact you shortly to confirm equipment dispatch, ID verification, and security deposit details.

Best regards,
GearShare Team
"""

        # Resolve Sender identity:
        # If EMAIL_FROM contains a placeholder or different address, ensure valid sender format
        configured_from = settings.EMAIL_FROM.strip()
        from_name, from_addr = email.utils.parseaddr(configured_from)
        if not from_addr or "your_gmail" in from_addr or "@" not in from_addr:
            from_name = from_name or "GearShare Rentals"
            from_addr = settings.SMTP_USERNAME
            sender_header = email.utils.formataddr((from_name, from_addr))
        else:
            sender_header = configured_from

        envelope_from = from_addr or settings.SMTP_USERNAME

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Rental Enquiry Received — GearShare"
        msg["From"] = sender_header
        msg["To"] = recipient_email
        msg["Date"] = email.utils.formatdate(localtime=False)
        msg["Message-ID"] = email.utils.make_msgid(domain="gearshare.com")

        part_text = MIMEText(plain_text, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

        server: Optional[smtplib.SMTP] = None
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()

            password = settings.SMTP_PASSWORD.get_secret_value()
            server.login(settings.SMTP_USERNAME, password)

            # sendmail: envelope_from, [recipient_email], msg.as_string()
            server.sendmail(envelope_from, [recipient_email], msg.as_string())

            logger.info(
                "Successfully dispatched confirmation email for %s to %s via SMTP (%s)",
                reference_id,
                recipient_email,
                settings.SMTP_HOST,
            )
            return True, None

        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error(
                "SMTP authentication failed while sending confirmation email for %s: %s",
                reference_id,
                auth_err.smtp_error.decode("utf-8", errors="replace") if isinstance(auth_err.smtp_error, bytes) else str(auth_err.smtp_error),
            )
            return False, "SMTP authentication failed"

        except smtplib.SMTPRecipientsRefused as rec_err:
            logger.error(
                "Recipient refused by SMTP server for %s (%s): %s",
                reference_id,
                recipient_email,
                rec_err,
            )
            return False, f"Recipient email refused: {recipient_email}"

        except smtplib.SMTPException as smtp_err:
            err_msg = str(smtp_err)
            logger.error(
                "SMTP error while sending confirmation email for %s: %s",
                reference_id,
                err_msg,
            )
            return False, f"SMTP error: {err_msg}"

        except Exception as exc:
            err_msg = str(exc)
            logger.error(
                "Unexpected failure sending confirmation email for %s via SMTP: %s",
                reference_id,
                err_msg,
            )
            return False, f"Failed to send email: {err_msg}"

        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
