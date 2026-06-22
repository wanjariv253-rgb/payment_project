from django.http import HttpResponse
from reportlab.pdfgen import canvas

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

    pdf = canvas.Canvas(response)

    pdf.setTitle("Payment Receipt")

    pdf.drawString(100, 800, "PAYMENT RECEIPT")
    pdf.drawString(100, 780, f"Gateway: {gateway}")
    pdf.drawString(100, 760, f"Transaction ID: {transaction.txnid}")
    pdf.drawString(100, 740, f"Customer Name: {transaction.customer_name}")
    pdf.drawString(100, 720, f"Loan Account No: {transaction.loan_ac_no}")
    pdf.drawString(100, 700, f"City: {transaction.city}")
    pdf.drawString(100, 680, f"Email: {transaction.email}")
    pdf.drawString(100, 660, f"Phone: {transaction.phone}")
    pdf.drawString(100, 640, f"Amount: Rs {transaction.amount}")
    pdf.drawString(100, 620, f"Status: {transaction.status}")
    pdf.drawString(100, 600, f"Date: {transaction.created_at}")

    pdf.save()

    return response