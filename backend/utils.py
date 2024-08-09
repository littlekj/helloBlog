import secrets


def generate_secret_key(length=50):
    return secrets.token_urlsafe(length)


print(generate_secret_key())
