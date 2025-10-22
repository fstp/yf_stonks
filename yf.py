#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "rich",
#   "protobuf",
#   "websockets",
# ]
# ///
# vim: ft=python
import asyncio
import base64
import binascii
import json

import websockets
from google.protobuf import message, text_format
from google.protobuf.message import DecodeError
from rich.console import Console
from rich.traceback import install

install(show_locals=True)

try:
    import pricing_pb2
except ImportError:
    print("Error: Could not import pricing_pb2.py.")
    print("Please compile the pricing.proto file first by running:")
    print("protoc --python_out=. pricing.proto")
    exit(1)


def decode_and_print_protobuf(encoded_string: str):
    """Decodes a Base64 string and parses it as a PricingData protobuf message."""
    console = Console()
    try:
        decoded_bytes = base64.b64decode(encoded_string)
        pricing_data = pricing_pb2.PricingData()
        pricing_data.ParseFromString(decoded_bytes)
        console.print("[bold green]Decoded Protobuf Data:[/bold green]")
        pretty_output = text_format.MessageToString(pricing_data)
        console.print(pretty_output)
    except binascii.Error as e:
        console.print(f"[bold red]Error:[/bold red] Invalid Base64 string. {e}")
    except DecodeError as e:
        console.print(f"[bold red]Protobuf Decode Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


console = Console()


async def main():
    url = "wss://streamer.finance.yahoo.com/"

    # Yahoo Finance expects specific query parameters
    params = {"version": "2", "environment": "protobuf"}

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{query_string}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://finance.yahoo.com",
    }

    try:
        console.print(f"[yellow]Connecting to {full_url}[/yellow]")

        async with websockets.connect(
            full_url, additional_headers=headers, ping_interval=20, ping_timeout=20
        ) as websocket:
            console.print("[green]Connected to Yahoo Finance WebSocket[/green]")

            # Subscribe to some symbols (example)
            subscribe_message = {
                "subscribe": [
                    "AAPL",
                    "TSLA",
                    "BYND",
                ]  # Add symbols you're interested in
            }

            await websocket.send(json.dumps(subscribe_message))
            console.print("[cyan]Sent subscription message[/cyan]")

            # Test with your sample data
            input_string = (
                "CgNBVlkVSOEwQxiwpPzMwWYqA05ZUTAIOAFFSZ4CQUiKnFploJlVQdgBBA=="
            )
            console.print(f"[cyan]Testing with sample data:[/cyan] {input_string}")
            decode_and_print_protobuf(input_string)

            # Listen for incoming messages
            async for message in websocket:
                if isinstance(message, str):
                    console.print(f"[blue]Received text message:[/blue] {message}")
                else:
                    # Assuming binary protobuf data
                    try:
                        # For binary data, you might need to decode it directly
                        console.print("[yellow]Received binary data[/yellow]")
                        # If it's base64 encoded text, decode it
                        if len(message) < 1000:  # heuristic for text vs binary
                            try:
                                text_data = message.decode("utf-8")
                                console.print(f"[blue]Decoded text:[/blue] {text_data}")
                            except:
                                pass
                    except Exception as e:
                        console.print(f"[red]Error processing message:[/red] {e}")

    except Exception as e:
        console.print(f"[red]Connection error:[/red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
