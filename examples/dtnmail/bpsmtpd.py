#!/usr/bin/env python3

import asyncio
from aiosmtpd.controller import Controller
import json
import argparse
import socket


class BpSmtpHandler:
    def __init__(
        self, domain="example.com", udp_out=("localhost", 10101), dtn_dst="ipn:2.25"
    ):
        self.domain = domain
        self.udp_out = udp_out
        self.dtn_dst = dtn_dst
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        print("Received MAIL FROM:", envelope.mail_from)
        print("           RCPT TO:", address)
        if not envelope.mail_from.endswith("@" + self.domain):
           return "550 not relaying to that domain"
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        print("Message from %s" % envelope.mail_from)
        print("Message for %s" % envelope.rcpt_tos)
        print("Message data:\n")
        for ln in envelope.content.decode("utf8", errors="replace").splitlines():
            print(f"> {ln}".strip())
        print()
        print("End of message")

        msg_content = {
            "from": envelope.mail_from,
            "to": envelope.rcpt_tos,
            "data": envelope.content.decode("utf8", errors="replace"),
        }
        msg = {
            "dst": self.dtn_dst,
            "content": json.dumps(msg_content),
        }
        msg_bytes = json.dumps(msg).encode("utf-8")
        print(
            f"Sending message of {len(msg_bytes)} bytes for {self.dtn_dst} via UDP to {self.udp_out}"
        )
        self.sock.sendto(msg_bytes, self.udp_out)

        return "250 Message accepted for delivery"


def main():
    parser = argparse.ArgumentParser(description="Run a simple SMTP server.")
    parser.add_argument(
        "--port", "-p", type=int, default=8025, help="Port to run the SMTP server on"
    )
    parser.add_argument(
        "--domain",
        "-d",
        type=str,
        default="example.com",
        help="Domain to relay emails for (default: example.com)",
    )
    parser.add_argument(
        "--udp-out",
        "-u",
        type=str,
        default="localhost:10101",
        help="UDP address to send messages to (default: localhost:10101)",
    )
    parser.add_argument(
        "--dtn-dst",
        "-D",
        type=str,
        default="ipn:2.25",
        help="DTN destination for the messages (default: ipn:2.25)",
    )
    args = parser.parse_args()

    out = args.udp_out.split(":")
    if len(out) != 2:
        print("Invalid UDP output address format. Use 'host:port'.")
        return
    out[1] = int(out[1])  # Convert port to integer
    out = tuple(out)
    controller = Controller(
        BpSmtpHandler(domain=args.domain, udp_out=out, dtn_dst=args.dtn_dst),
        port=args.port,
        hostname="localhost",
    )
    print(f"Starting SMTP server on port {args.port} for domain {args.domain}...")
    controller.start()
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("Stopping SMTP server...")
        controller.stop()


if __name__ == "__main__":
    main()
