#!/usr/bin/env python3

import argparse

from smtplib import SMTP as Client

parser = argparse.ArgumentParser(
    description="Send an email using a simple SMTP client."
)
parser.add_argument(
    "--hostname", "-H", type=str, default="localhost", help="SMTP server hostname"
)
parser.add_argument("--port", "-p", type=int, default=8025, help="SMTP server port")
parser.add_argument(
    "--from-email", "-f", type=str, default="a@example.com", help="Sender email address"
)
parser.add_argument(
    "--to-email",
    "-t",
    type=str,
    nargs="+",
    default=["b@example.com"],
    help="Recipient email addresses",
)
parser.add_argument(
    "--subject",
    "-s",
    type=str,
    default="A test",
    help="Subject of the email",
)
parser.add_argument(
    "--body",
    "-b",
    type=str,
    default="Just a test email.",
    help="Body of the email",
)

args = parser.parse_args()

client = Client(args.hostname, args.port)
r = client.sendmail(
    args.from_email,
    args.to_email,
    f"""\
From: {args.from_email}
To: {", ".join(args.to_email)}
Subject: {args.subject}
Message-ID: <ant>

{args.body}
""",
)
print("Sendmail result:", r)
if r:
    print("Some emails were not delivered:", r)
