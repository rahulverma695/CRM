from typing import Protocol


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Dev/test sender. Records sent messages and prints them."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})
        print(f"[email] to={to} subject={subject}\n{body}")


# Module-level singleton used by the app; tests can inspect `.sent`.
email_sender = ConsoleEmailSender()


def get_email_sender() -> EmailSender:
    return email_sender
