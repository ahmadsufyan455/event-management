from datetime import timedelta, timezone
from celery import shared_task
from django.core.mail import EmailMultiAlternatives

from events.models import Event
from registrations.models import Registration

from django.utils.dateparse import parse_datetime
from loguru import logger


@shared_task
def send_ticket_email(user_email, username, registration_id):
    logger.info(
        f"Starting send_ticket_email task: registration_id={registration_id}, email={user_email}, username={username}"
    )

    try:
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

        logger.info(f"Preparing email for registration {registration_id} to {user_email}")
        email = EmailMultiAlternatives(subject, text_content, "no-reply@dicoevent.com", [user_email])
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Email sent successfully to {user_email} for registration {registration_id}")
        return f"Email sent to {user_email}"
    except Exception as e:
        logger.error(
            f"Error sending ticket email to {user_email} for registration {registration_id}: {e}", exc_info=True
        )
        raise


@shared_task
def send_event_reminder_email(user_email, username, event_start_time_str):
    logger.info(
        f"Starting send_event_reminder_email task: email={user_email}, username={username}, event_start_time={event_start_time_str}"
    )

    try:
        event_start_time = parse_datetime(event_start_time_str)
        if not event_start_time:
            raise ValueError(f"Invalid event_start_time format: {event_start_time_str}")

        subject = f"Pengingat: Event Dimulai dalam 2 Jam"

        formatted_time = event_start_time.strftime("%d %B %Y, pukul %H:%M WIB")

        text_content = f"""Halo {username},

    Ini adalah pengingat bahwa event yang Anda daftarkan akan dimulai dalam 2 jam!

    - Waktu Mulai: {formatted_time}

    Silakan datang 30 menit sebelum event dimulai untuk melakukan pembayaran dan check-in.

    Kami tunggu kedatangan Anda!

    Terima kasih,
    Tim Dico Event

    Pesan ini dikirim secara otomatis. Mohon tidak membalas pesan ini.
    """

        html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #E50914; text-align: center;">⏰ Pengingat Event</h2>
                    <p>Halo <strong>{username}</strong>,</p>
                    <p>Ini adalah pengingat bahwa event yang Anda daftarkan akan dimulai dalam <strong>2 jam</strong>!</p>
                    
                    <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Detail Event:</strong></p>
                        <p><strong>Waktu Mulai:</strong> {formatted_time}</p>
                    </div>
                    
                    <p>Silakan datang <strong>30 menit sebelum event dimulai</strong> untuk melakukan pembayaran dan check-in.</p>
                    <p>Kami tunggu kedatangan Anda! 🎉</p>
                    
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

        logger.info(f"Preparing reminder email for {user_email}, event starts at {formatted_time}")
        email = EmailMultiAlternatives(subject, text_content, "no-reply@dicoevent.com", [user_email])
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Reminder email sent successfully to {user_email}")
        return f"Reminder email sent to {user_email}"
    except Exception as e:
        logger.error(f"Error sending reminder email to {user_email}: {e}", exc_info=True)
        raise


@shared_task
def send_event_reminders():
    logger.info("Starting send_event_reminders scheduled task")

    try:
        now = timezone.now()
        two_hours_from_now = now + timedelta(hours=2)

        time_window_start = two_hours_from_now - timedelta(minutes=15)
        time_window_end = two_hours_from_now + timedelta(minutes=15)

        logger.info(f"Checking for events starting between {time_window_start} and {time_window_end}")

        upcoming_events = Event.objects.filter(
            start_time__gte=time_window_start,
            start_time__lte=time_window_end,
            status="scheduled",
        ).select_related("organizer")

        event_count = upcoming_events.count()
        logger.info(f"Found {event_count} upcoming events in the time window")

        sent_count = 0

        for event in upcoming_events:
            logger.info(f"Processing event {event.id}: {event.name}, start_time: {event.start_time}")
            registrations = Registration.objects.filter(ticket__event=event).select_related("user")
            registration_count = registrations.count()
            logger.info(f"Found {registration_count} registrations for event {event.id}")

            for registration in registrations:
                try:
                    send_event_reminder_email.delay(
                        registration.user.email,
                        registration.user.username,
                        event.start_time.isoformat(),
                    )
                    sent_count += 1
                    logger.debug(
                        f"Queued reminder email for registration {registration.id}, user: {registration.user.email}"
                    )
                except Exception as e:
                    logger.error(f"Error queuing reminder email for registration {registration.id}: {e}", exc_info=True)

        result = f"Processed {event_count} events, sent {sent_count} reminders"
        logger.info(result)
        return result
    except Exception as e:
        logger.error(f"Error in send_event_reminders task: {e}", exc_info=True)
        raise
