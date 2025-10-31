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
import signal
import sys

import websockets
from google.protobuf import text_format
from google.protobuf.message import DecodeError
from rich.console import Console
from rich.prompt import Prompt
from rich.traceback import install

install(show_locals=True)

console = Console()

try:
    import pricing_pb2
except ImportError:
    print("Error: Could not import pricing_pb2.py.")
    print("Please compile the pricing.proto file first by running:")
    print("protoc --python_out=. pricing.proto")
    exit(1)


def decode_and_print_protobuf(encoded_string: str):
    """Decodes a Base64 string and parses it as a PricingData protobuf message."""
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


async def main():
    # Get symbol from command line argument, default to "BYND" if not provided
    symbol = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    old_symbol = symbol
    url = "wss://streamer.finance.yahoo.com/"

    params = {"version": "2", "environment": "protobuf"}

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{query_string}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Origin": "https://finance.yahoo.com",
    }

    console.print(f"[yellow]Connecting to {full_url}[/yellow]")

    shutdown_requested = False
    unsubscribe_requested = False

    async with websockets.connect(
        full_url, additional_headers=headers, ping_interval=20, ping_timeout=20
    ) as websocket:
        console.print("[green]Connected to Yahoo Finance WebSocket[/green]")

        def signal_handler():
            nonlocal shutdown_requested
            nonlocal unsubscribe_requested
            nonlocal symbol
            nonlocal old_symbol
            if not (shutdown_requested or unsubscribe_requested):
                console.print("\n[yellow]Interrupt...[/yellow]")
                response = Prompt.ask(
                    "c(ontinue), q(uit), a(dd)", default="c", choices=["c", "q", "a"]
                )
                if response.lower() == "q":
                    asyncio.create_task(websocket.close())
                    shutdown_requested = True
                elif response.lower() == "a":
                    unsubscribe_requested = True
                    old_symbol = symbol
                    symbol = Prompt.ask("Symbol", default="SPY")
                else:
                    console.print("[green]Continuing...[/green]")

        # Register signal handlers
        loop = asyncio.get_running_loop()
        # for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signal.SIGINT, signal_handler)

        # unsubscribe_message = {
        #     "unsubscribe": ["^GSPC","^DJI","^IXIC","^RUT",
        #                     "^VIX","GC=F","WOLF","KLAR",
        #                     "VICR","ISRG","TNL","PEGA",
        #                     "AVY","HUT","LEU","OKLO",
        #                     "GLXY","CIFR"]
        # }
        # subscribe_message = {
        #     "subscribe": [
        #         symbol
        #         # "AAPL",
        #         # "TSLA",
        #         # "BYND",
        #         # "SPY",
        #         # "BYND251024C00000500"
        #     ]
        # }

        console.print(f"[green]Subscribed to [cyan]{symbol}[/cyan][/green]")
        subscribe_message = {"subscribe": [symbol]}
        await websocket.send(json.dumps(subscribe_message))

        # input_string = (
        #     "CgNBVlkVSOEwQxiwpPzMwWYqA05ZUTAIOAFFSZ4CQUiKnFploJlVQdgBBA=="
        # )
        # console.print(f"[cyan]Testing with sample data:[/cyan] {input_string}")
        # decode_and_print_protobuf(input_string)

        async for message in websocket:
            if shutdown_requested:
                break
            if unsubscribe_requested:
                unsubscribe_requested = False
                unsubscribe_message = {"unsubscribe": [old_symbol]}
                await websocket.send(json.dumps(unsubscribe_message))
                subscribe_message = {"subscribe": [symbol]}
                await websocket.send(json.dumps(subscribe_message))
                console.clear(home=True)
                console.print(
                    f"[yellow]Unsubscribed from [cyan]{old_symbol}[/cyan][/yellow]"
                )
                console.print(f"[green]Subscribed to [cyan]{symbol}[/cyan][/green]")
                continue
            try:
                console.print(f"[blue]Received text message:[/blue] {message}")
                json_data = json.loads(message)
                decode_and_print_protobuf(json_data["message"])
            except Exception as e:
                console.print(f"[red]Error processing message:[/red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
