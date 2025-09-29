#!/usr/bin/env python3


import asyncio
import socket
import threading
import json
import argparse


class SimpleIMAPServer:
    def __init__(self, host="127.0.0.1", port=143, udp_in: int = 10202, domain="example.com"):
        self.domain = domain
        self.host = host
        self.port = port
        self.mailboxes = {}  # Store mailboxes as dictionaries
        # add a default mailbox
        self.mailboxes["INBOX"] = {}
        # add a random message to the default mailbox
        self.mailboxes["INBOX"][
            1
        ] = "From: a@example.com\r\nTo: b@example.com\r\nSubject: Test\r\n\r\nThis is a test message.\r\n"

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, udp_in))

        threading.Thread(target=self.udp_receiver, daemon=True).start()

    def udp_receiver(self):
        print(f"UDP receiver started on {self.host}:{self.port}")
        while True:
            data, addr = self.sock.recvfrom(65535)  # Buffer size of 65535 bytes
            if data:
                print(f"Received UDP message from {addr}: {data.decode()}")
                self.mailboxes["INBOX"][len(self.mailboxes["INBOX"]) + 1] = json.loads(
                    data.decode()
                )[
                    "data"
                ]  # Store the message in INBOX
                print(self.mailboxes["INBOX"])

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"Connection from {addr}")

        try:
            await self.send_greeting(writer)

            while True:
                data = await reader.readline()
                if not data:
                    break

                message = data.decode().strip()
                print(f"< {message}")
                code, message = (
                    message.split(" ", 1) if " " in message else (message, "")
                )

                if message.upper().startswith("LOGIN"):
                    await self.handle_login(
                        message,
                        code,
                        writer,
                    )
                elif message.upper().startswith("CAPABILITY"):
                    await self.handle_capability(code, writer)
                elif message.upper().startswith("LIST"):
                    await self.handle_list(code, message, writer)
                elif message.upper().startswith("SELECT"):
                    await self.handle_select(message, code, writer)
                elif message.upper().startswith("CLOSE"):
                    await self.handle_close(code, writer)
                elif message.upper().startswith("SEARCH"):
                    await self.handle_search(message, code, writer)
                elif message.upper().startswith("FETCH"):
                    await self.handle_fetch(message, code, writer)
                elif message.upper().startswith("LOGOUT"):
                    await self.handle_logout(code, writer)
                    break
                else:
                    await self.send_response(writer, "BAD Command not recognized.")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"Connection from {addr} closed")

    async def send_greeting(self, writer):
        await self.send_response(writer, "* OK Simple IMAP Server Ready")

    async def handle_capability(self, code, writer):
        capabilities = [
            "IMAP4rev1",
            "STARTTLS",
            "AUTH=PLAIN",
            "IDLE",
            "NAMESPACE",
            "LIST-EXTENDED",
        ]
        await self.send_response(writer, f"* CAPABILITY {' '.join(capabilities)}")
        await self.send_response(writer, f"{code} OK CAPABILITY completed")

    async def handle_login(self, message, code, writer):
        print(f"Handling LOGIN: {message}")
        parts = message.split()
        if len(parts) != 3:
            await self.send_response(
                writer, f"{code} BAD LOGIN command requires username and password"
            )
            return

        username, password = parts[1], parts[2]

        if username == "test" and password == '"test"':
            await self.send_response(writer, f"{code} OK LOGIN completed")
            self.current_user = username
        else:
            await self.send_response(writer, f"{code} NO LOGIN failed")

    async def handle_list(self, message, code, writer):
        print(f"Handling LIST: {message}")
        await self.send_response(writer, '* LIST () "." INBOX')
        await self.send_response(writer, f"{message} OK LIST completed")

    async def handle_select(self, message, code, writer):
        parts = message.split()
        if len(parts) != 2:
            await self.send_response(
                writer, f"{code} BAD SELECT command requires mailbox name"
            )
            return
        mailbox = parts[1]
        if mailbox not in self.mailboxes:
            self.mailboxes[mailbox] = {}
        await self.send_response(writer, f"* {len(self.mailboxes[mailbox])} EXISTS")
        await self.send_response(writer, f"{code} OK [READ-WRITE] SELECT completed")
        self.current_mailbox = mailbox

    async def handle_close(self, code, writer):
        if self.current_mailbox is None:
            await self.send_response(writer, f"{code} NO SELECT command must be issued")
            return
        await self.send_response(writer, f"{code} OK CLOSE completed")
        self.current_mailbox = None

    async def handle_search(self, message, code, writer):
        parts = message.split()
        if len(parts) < 2:
            await self.send_response(
                writer, f"{code} BAD SEARCH command requires search criteria"
            )
            return
        if self.current_mailbox is None:
            await self.send_response(writer, f"{code} NO SELECT command must be issued")
            return

        # For simplicity, we assume all messages match the search criteria
        msg_nums = list(self.mailboxes[self.current_mailbox].keys())
        await self.send_response(writer, f"* SEARCH {' '.join(map(str, msg_nums))}")
        await self.send_response(writer, f"{code} OK SEARCH completed")

    async def handle_fetch(self, message, code, writer):
        parts = message.split()
        if len(parts) != 3:
            await self.send_response(
                writer,
                f"{code} BAD FETCH command requires message number and data item",
            )
            return
        try:
            msg_num = int(parts[1])
        except ValueError:
            await self.send_response(
                writer, f"{code} BAD FETCH command requires a valid message number"
            )
            return
        if self.current_mailbox is None:
            await self.send_response(writer, f"{code} NO SELECT command must be issued")
            return

        if msg_num not in self.mailboxes[self.current_mailbox]:
            await self.send_response(writer, f"{code} NO Message not found")
            return

        msg = self.mailboxes[self.current_mailbox][msg_num]
        await self.send_response(
            writer, f"* {msg_num} FETCH (RFC822 {{{len(msg)}}}\r\n{msg})"
        )
       
        await self.send_response(writer, f"{code} OK FETCH completed")

    async def handle_logout(self, code, writer):
        await self.send_response(writer, "* BYE Simple IMAP Server Closing")
        await self.send_response(writer, f"{code} OK LOGOUT completed")
        self.current_user = None
        self.current_mailbox = None

    async def send_response(self, writer, message):
        print(f"> {message}")
        writer.write(f"{message}\r\n".encode())
        await writer.drain()

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with server:
            await server.serve_forever()


async def main():
    parser = argparse.ArgumentParser(description="Run a simple DTN IMAP server.")
    parser.add_argument("--host", "-H", type=str, default="localhost")
    parser.add_argument("--port", "-p", type=int, default=1143)
    parser.add_argument(
        "--udp-in", "-u", type=int, default=10202, help="UDP port for incoming messages"
    )
    parser.add_argument(
        "--domain",
        "-d",
        type=str,
        default="example.com",
        help="Domain to relay emails for (default: example.com)",
    )
    args = parser.parse_args()

    server = SimpleIMAPServer(host=args.host, port=args.port, udp_in=args.udp_in, domain=args.domain)
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.sleep(0)  # Allow the event loop to run
# This line is necessary to keep the event loop running
