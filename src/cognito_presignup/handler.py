ALLOWED_DOMAIN = "@altostratus.es"


def handler(event, context):
    email = event["request"]["userAttributes"].get("email", "")

    if not email.lower().endswith(ALLOWED_DOMAIN):
        raise Exception(f"Solo se permiten registros con correo {ALLOWED_DOMAIN}")

    return event
