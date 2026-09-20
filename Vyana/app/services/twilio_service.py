from xml.sax.saxutils import escape

from twilio.base.exceptions import TwilioRestException
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

from app.core.config import settings


def twilio_is_configured() -> bool:
    return settings.twilio_is_configured()


def _build_twiml(message: str) -> str:
    safe_message = escape(message)
    return f"""<Response>
  <Say language=\"hi-IN\" voice=\"Polly.Aditi\">{safe_message}</Say>
</Response>"""


def place_test_call(
    to_number: str | None = None,
    message: str | None = None,
    use_local_webhook: bool = False,
) -> dict:
    account_sid = settings.twilio_account_sid
    auth_token = settings.twilio_auth_token
    from_number = settings.twilio_from_number
    default_to_number = settings.twilio_to_number

    if not all([account_sid, auth_token, from_number]):
        raise ValueError("Missing Twilio configuration. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER.")

    destination_number = (to_number or default_to_number).strip()
    if not destination_number:
        raise ValueError("Missing destination number. Set TWILIO_TO_NUMBER or pass to_number.")

    call_message = message or (
        "Vyana Care test call. Yeh aapki Twilio integration verification hai."
    )

    http_client = TwilioHttpClient(timeout=20.0, max_retries=0)
    client = Client(account_sid, auth_token, http_client=http_client)

    try:
        if use_local_webhook:
            webhook_url = settings.twilio_webhook_url
            if not webhook_url:
                raise ValueError("use_local_webhook=true requires TWILIO_WEBHOOK_URL to be set to a public URL.")
            call = client.calls.create(to=destination_number, from_=from_number, url=webhook_url)
            mode = "webhook"
        else:
            call = client.calls.create(to=destination_number, from_=from_number, twiml=_build_twiml(call_message))
            mode = "twiml"
    except TwilioRestException as exc:
        raise RuntimeError(f"{exc.msg} (code {exc.code})") from exc

    return {
        "mode": mode,
        "call_sid": call.sid,
        "status": call.status,
        "from_number": from_number,
        "to_number": destination_number,
        "message": call_message,
    }