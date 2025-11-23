from celery import shared_task
from django.core.mail import EmailMultiAlternatives


@shared_task
def send_ticket_email(user_email, username, registration_id):
    subject = f"Konfirmasi Registrasi Event"

    text_content = f"""Halo {username},
 
    Terima kasih telah melakukan registrasi event!
 
    Berikut adalah detail pemesanan tiket Anda:
 
    ID Pemesanan: {registration_id}
 
    Silakan datang ke event 30 menit sebelum event dimulai untuk melakukan pembayaran.
 
    Kami tunggu kedatangan Anda, selamat menikmati event!
 
    Terima kasih,
    Tim Dico Event
 
    Pesan ini dikirim secara otomatis. Mohon tidak membalas pesan ini.
    """

    # HTML formatted version
    html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #E50914; text-align: center;">Konfirmasi Registrasi Event</h2>
                <p>Halo <strong>{username}</strong>,</p>
                <p>Terima kasih telah melakukan registrasi event di <strong>Dico Event</strong>!</p>
                <p><strong>Detail Registrasi Anda:</strong></p>
                <p style="background-color: #f8f8f8; padding: 10px; border-radius: 5px;">
                    <strong>ID Registrasi:</strong> {registration_id}
                </p>
                <p>Silakan datang <strong>30 menit sebelum event dimulai</strong> untuk melakukan pembayaran.</p>
                <p>Kami tunggu kedatangan Anda, selamat menikmati event!</p>
                <br>
                <p style="font-size: 12px; color: #777; text-align: center;">
                    Pesan ini dikirim secara otomatis. Mohon tidak membalas pesan ini.
                </p>
                <p style="font-size: 12px; color: #777; text-align: center;">
                    <strong>Dico Event Team</strong>
                </p>
            </div>
        </body>
        </html>
        """

    email = EmailMultiAlternatives(subject, text_content, "no-reply@dicoevent.com", [user_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
    return f"Email sent to {user_email}"
