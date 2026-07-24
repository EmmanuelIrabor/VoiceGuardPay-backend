import os

from securepay import SecurePayApi, SecurePayConfig


def get_client() -> SecurePayApi:
    api_key = os.environ.get("SECUREPAY_API_KEY")
    if not api_key:
        raise RuntimeError("SECUREPAY_API_KEY is not set")

    env = os.environ.get("SECUREPAY_ENV", "production")
    config = SecurePayConfig.production() if env == "production" else SecurePayConfig.staging()

    return SecurePayApi(api_key=api_key, config=config)


def initiate_payment(recipient_name: str, account_number: str, amount: float, narration: str = ""):
    client = get_client()
    raise NotImplementedError