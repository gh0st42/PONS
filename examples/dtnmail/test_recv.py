#!/usr/bin/env python3

import imaplib
import email
import argparse

# Argument parser for command line options
parser = argparse.ArgumentParser(
    description="Receive and display emails from an IMAP server."
)
parser.add_argument(
    "--hostname", "-H", type=str, default="localhost", help="IMAP server hostname"
)
parser.add_argument("--port", "-p", type=int, default=143, help="IMAP server port")
parser.add_argument(
    "--email", "-e", type=str, default="test", help="Email address for login"
)
parser.add_argument(
    "--password", "-P", type=str, default="test", help="Password for the email account"
)   
args = parser.parse_args()

# IMAP server details
imap_server = args.hostname
imap_port = args.port
email_address = args.email
password = args.password

# Connect to the IMAP server
try:
    mail = imaplib.IMAP4(imap_server, imap_port)
    mail.debug = 0  # Set debug level to see detailed output
    mail.login(email_address, password)
    print("Connected to IMAP server successfully.")
except imaplib.IMAP4.error as e:
    print("Authentication failed.", e)
    exit()
except Exception as e:
    print(f"An error occurred: {e}")
    exit()

print("Listing mailboxes...")
# List mailboxes
r = mail.list()
print("Mailboxes:", r)

print("Selecting inbox...")
# Select a mailbox (e.g., "inbox")
mail.select("INBOX")

print("Searching for emails...")
# Search for emails (e.g., all emails)
result, data = mail.search(None, "ALL")

# Iterate through the emails
email_ids = data[0].split()
for email_id in email_ids:
    # Fetch the email
    result, email_data = mail.fetch(email_id, "(RFC822)")
    raw_email = email_data[0][1]

    # Parse the email
    msg = email.message_from_bytes(raw_email)

    # Print email information
    print(f"From: {msg['from']}")
    print(f"To: {msg['to']}")
    print(f"Subject: {msg['subject']}")

    # Print the body of the email
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                print(f"Body: {body}")
    else:
        body = msg.get_payload(decode=True).decode()
        print(f"Body: {body}")
    print("-" * 20)

# Close the connection
mail.close()
mail.logout()
print("Disconnected from IMAP server.")
