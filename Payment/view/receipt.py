from datetime import datetime
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from Payment.model.payment_easebuzz import Transaction_easebuzz
from Payment.model.payment_payu import Transaction


def download_receipt(request, txnid):

    # Pehle Easebuzz me check karo
    transaction = Transaction_easebuzz.objects.filter(
        txnid=txnid
    ).first()

    gateway = "Easebuzz"

    # Agar Easebuzz me nahi mila to PayU me check karo
    if not transaction:
        transaction = Transaction.objects.filter(
            txnid=txnid
        ).first()
        gateway = "PayU"

    if not transaction:
        return HttpResponse(
            "Transaction not found",
            status=404
        )

    response = HttpResponse(
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename=receipt_{txnid}.pdf'
    )

    # PDF Canvas
    pdf = canvas.Canvas(response)
    pdf.setTitle("Payment Receipt")

    # =========================
    # COLOR PALETTE
    # =========================
    primary_color = HexColor("#1E3A8A")
    text_dark = HexColor("#1E293B")
    text_muted = HexColor("#64748B")
    border_color = HexColor("#E2E8F0")
    bg_light = HexColor("#F8FAFC")
    success_green = HexColor("#059669")
    success_bg = HexColor("#ECFDF5")

    # =========================
    # HEADER SECTION
    # =========================
    pdf.setFillColor(primary_color)
    pdf.rect(40, 730, 515, 65, stroke=0, fill=1)

    pdf.setFillColor(HexColor("#FFFFFF"))
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(60, 755, "PAYMENT RECEIPT")

    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(
        535,
        755,
        f"Gateway: {gateway}"
    )

    # =========================
    # RECEIPT ROW FUNCTION
    # =========================
    y_pos = 680

    def draw_receipt_row(pdf, label, value, current_y):

        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(text_muted)
        pdf.drawString(60, current_y, label)

        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(text_dark)

        if label == "Transaction ID:":
            pdf.setFont("Helvetica-Bold", 10)

        pdf.drawString(
            210,
            current_y,
            str(value) if value else "-"
        )

        pdf.setStrokeColor(border_color)
        pdf.setLineWidth(0.5)

        pdf.line(
            60,
            current_y - 8,
            535,
            current_y - 8
        )

        return current_y - 28

    # =========================
    # DATE FORMAT
    # =========================
    date_display = str(transaction.created_at)

    if hasattr(transaction.created_at, "strftime"):
        date_display = transaction.created_at.strftime(
            "%d %B %Y, %I:%M %p"
        )

    # =========================
    # TRANSACTION DETAILS
    # =========================
    y_pos = draw_receipt_row(
        pdf,
        "Transaction ID:",
        transaction.txnid,
        y_pos
    )

    y_pos = draw_receipt_row(
        pdf,
        "Loan Account No:",
        getattr(transaction, "loan_ac_no", "-"),
        y_pos
    )

    y_pos = draw_receipt_row(
        pdf,
        "Customer Name:",
        getattr(transaction, "customer_name", "-"),
        y_pos
    )

    y_pos = draw_receipt_row(
        pdf,
        "City / Location:",
        getattr(transaction, "city", "-"),
        y_pos
    )

    y_pos = draw_receipt_row(
        pdf,
        "Email Address:",
        transaction.email,
        y_pos
    )

    y_pos = draw_receipt_row(
        pdf,
        "Phone Number:",
        transaction.phone,
        y_pos
    )

    # =========================
    # AMOUNT & STATUS BOX
    # =========================
    y_pos -= 15

    pdf.setFillColor(bg_light)
    pdf.setStrokeColor(border_color)
    pdf.setLineWidth(1)

    pdf.roundRect(
        60,
        y_pos - 45,
        475,
        55,
        6,
        stroke=1,
        fill=1
    )

    pdf.setFillColor(text_dark)
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(
        80,
        y_pos - 22,
        "TOTAL AMOUNT PAID:"
    )

    pdf.setFillColor(primary_color)
    pdf.setFont("Helvetica-Bold", 15)

    pdf.drawString(
        230,
        y_pos - 24,
        f"₹ {transaction.amount}"
    )

    # =========================
    # STATUS BADGE
    # =========================
    pdf.setFillColor(success_bg)
    pdf.setStrokeColor(HexColor("#A7F3D0"))

    pdf.roundRect(
        415,
        y_pos - 30,
        100,
        24,
        4,
        stroke=1,
        fill=1
    )

    pdf.setFillColor(success_green)
    pdf.setFont("Helvetica-Bold", 9)

    status_text = (
        str(transaction.status).upper()
        if transaction.status
        else "SUCCESS"
    )

    pdf.drawCentredString(
        465,
        y_pos - 22,
        status_text
    )

    # =========================
    # NOTE SECTION
    # =========================
    y_pos -= 100

    pdf.setFillColor(HexColor("#EFF6FF"))
    pdf.setStrokeColor(HexColor("#BFDBFE"))

    pdf.roundRect(
        60,
        y_pos,
        475,
        38,
        6,
        stroke=1,
        fill=1
    )

    pdf.setFillColor(HexColor("#1D4ED8"))
    pdf.setFont("Helvetica", 8.5)

    pdf.drawString(
        75,
        y_pos + 22,
        "Note: This receipt is for your records. It may take 24-48 hours for the balance"
    )

    pdf.drawString(
        75,
        y_pos + 10,
        "to be updated in your loan account balance."
    )

    # =========================
    # FOOTER
    # =========================
    pdf.setFillColor(text_muted)
    pdf.setFont("Helvetica", 8)
    current_year = datetime.now().year

    pdf.drawCentredString(
    297,
    50,
    f"© {current_year} | All Rights Reserved | Terms and Conditions | Cancellation and Refund Policy     •     Designed & Developed by Berar Finance Limited"
    )

    # =========================
    # SAVE PDF
    # =========================
    pdf.showPage()
    pdf.save()

    return response