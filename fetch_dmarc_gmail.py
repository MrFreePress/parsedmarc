#!/usr/bin/env python3
"""
Script to fetch DMARC reports from Gmail using IMAP.

Usage:
    python fetch_dmarc_gmail.py

Prerequisites:
    - Gmail account with "Less secure app access" disabled (use App Password instead)
    - Go to https://myaccount.google.com/apppasswords to create an App Password
    - Enable IMAP in Gmail settings: Settings -> See all settings -> Forwarding and POP/IMAP
    - Create a Gmail label called "DMARC" and apply it to your DMARC report emails

Install dependencies:
    pip install imapclient

"""

import email
from email import policy
from imapclient import IMAPClient

# Gmail IMAP settings - UPDATE THESE VALUES
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
IMAP_USER = "your-email@gmail.com"  # Your Gmail address
IMAP_PASSWORD = "your-app-password"  # Gmail App Password (16 chars, no spaces)
FOLDER = "DMARC"  # Gmail label name where DMARC reports are stored


def main():
    print(f"Connecting to {IMAP_HOST}:{IMAP_PORT}...")

    try:
        # Connect to Gmail IMAP server
        client = IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True)
        client.login(IMAP_USER, IMAP_PASSWORD)
        print(f"Successfully logged in as {IMAP_USER}")

        # List all folders/labels
        print("\nAvailable folders/labels:")
        folders = client.list_folders()
        for flags, delimiter, name in folders:
            print(f"  - {name}")

        # Select the DMARC folder
        print(f"\nSelecting folder: {FOLDER}")
        try:
            select_info = client.select_folder(FOLDER, readonly=True)
            print(f"Folder '{FOLDER}' contains {select_info[b'EXISTS']} messages")
        except Exception as e:
            print(f"Error selecting folder '{FOLDER}': {e}")
            print("\nTrying with Gmail label format '[Gmail]/DMARC'...")
            # Try different folder name formats
            for attempt in [f"[Gmail]/{FOLDER}", FOLDER, f"INBOX.{FOLDER}"]:
                try:
                    select_info = client.select_folder(attempt, readonly=True)
                    print(f"Found folder: {attempt} with {select_info[b'EXISTS']} messages")
                    break
                except Exception:
                    continue
            else:
                print(f"Could not find folder {FOLDER}")
                client.logout()
                return

        # Search for all messages in the folder
        print("\nFetching messages...")
        messages = client.search(['ALL'])
        print(f"Found {len(messages)} messages")

        if not messages:
            print("No messages found in the DMARC folder")
            client.logout()
            return

        # Fetch and display message info
        print("\nMessage details:")
        print("-" * 80)

        for msg_id in messages[:10]:  # Limit to first 10 messages
            # Fetch the email
            response = client.fetch([msg_id], ['RFC822', 'ENVELOPE'])

            for uid, data in response.items():
                envelope = data[b'ENVELOPE']
                raw_email = data[b'RFC822']

                # Parse the email
                msg = email.message_from_bytes(raw_email, policy=policy.default)

                print(f"\nMessage ID: {uid}")
                print(f"  Subject: {envelope.subject.decode() if envelope.subject else 'N/A'}")
                print(f"  From: {envelope.from_[0] if envelope.from_ else 'N/A'}")
                print(f"  Date: {envelope.date}")

                # Check for attachments (DMARC reports are usually ZIP or XML)
                attachments = []
                for part in msg.walk():
                    content_disposition = part.get("Content-Disposition")
                    if content_disposition and "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            attachments.append(filename)

                if attachments:
                    print(f"  Attachments: {', '.join(attachments)}")

        print("-" * 80)
        print(f"\nTotal messages in {FOLDER}: {len(messages)}")

        client.logout()
        print("\nDisconnected from Gmail")

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
