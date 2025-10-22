#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "rich",
#   "protobuf",
#   "python-socketio[asyncio_client]",
# ]
# ///
# vim: ft=python
import asyncio
import base64
import binascii

import socketio
from google.protobuf import message, text_format
from google.protobuf.message import DecodeError
from rich.console import Console
from rich.traceback import install

install(show_locals=True)

# This script now depends on a compiled protobuf file.
# You MUST generate it first by running:
# protoc --python_out=. pricing.proto
try:
    import pricing_pb2
except ImportError:
    print("Error: Could not import pricing_pb2.py.")
    print("Please compile the pricing.proto file first by running:")
    print("protoc --python_out=. pricing.proto")
    exit(1)


def decode_and_print_protobuf(encoded_string: str):
    """
    Decodes a Base64 string and parses it as a PricingData protobuf message.
    """
    console = Console()

    try:
        # 1. Decode the Base64 string into bytes
        decoded_bytes = base64.b64decode(encoded_string)

        # 2. Create an instance of our Protobuf message
        pricing_data = pricing_pb2.PricingData()

        # 3. Parse the decoded bytes into the message object
        pricing_data.ParseFromString(decoded_bytes)

        # 4. Print the result using rich
        console.print("[bold green]Decoded Protobuf Data:[/bold green]")

        # Use text_format to pretty-print the protobuf object
        pretty_output = text_format.MessageToString(pricing_data)
        console.print(pretty_output)

    except binascii.Error as e:
        # Handle potential decoding errors (e.g., invalid padding)
        console.print(f"[bold red]Error:[/bold red] Invalid Base64 string. {e}")
    except DecodeError as e:
        # Handle errors if the bytes are not a valid PricingData message
        console.print(
            f"[bold red]Protobuf Decode Error:[/bold red] The data is not a valid PricingData message. {e}"
        )
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


# url = "wss://streamer.finance.yahoo.com/?version=2"
url = "wss://streamer.finance.yahoo.com/?version=2"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": "https://finance.yahoo.com",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive, Upgrade",
    "Upgrade": "websocket",
    "Cookie": "A1=d=AQABBNUAn2gCEBlZ68MYcYqLSZKWr3f-An0FEgABCAEz-mgjafU70CMA9qMCAAcI1QCfaHf-An0&S=AQAAAuLpqsKZ0ZKymfoHwORvTNg; A3=d=AQABBNUAn2gCEBlZ68MYcYqLSZKWr3f-An0FEgABCAEz-mgjafU70CMA9qMCAAcI1QCfaHf-An0&S=AQAAAuLpqsKZ0ZKymfoHwORvTNg; _ebd=YmlkLTdxMG51ZXRrOXUwNmwmZD1lMmE4MmQxODMyOGY3Yjc1ODBmOWE4ZTcyYzVkYmZlZiZ2PTE=; dflow=38; _dmit=BGYrRtLEubka7OBIoviNR90FjYIb0FjYIhqC9RaG5AFAIgqACAAAAAAAAAAAAAAAAAAAAAiAAEAABNoQHkAAiAAA.bid-7q0nuetk9u06l.eyJvIjoiYmlkLTdxMG51ZXRrOXUwNmwifQ==.1757680133495~CMEUCIBUxQQdxmhFEFfVYedttTgdhCD2q4SRfPKL86/O02R5+AiEA7Yg7lgDu9S3tpEN+9FQQlAE2IFcUt5FwulwBBGispg4=; _dmieu=CQWMLUAQWMLUAAOABBENB7FoAP_gAEPgACiQKZNB9G7WTWFjeTp2YPskOYwH0VBJ4MAwBgCBAUABzBIUIBwGRmAxJAyIICACGAIAIGBBIABlGABAQEAAIIAFAABIAEgAIBAAICAAAAAAAABACAAAAAAAAAAQgEAVMBQgmAYEBFoIQUhAggAAAQAAAAAEAIABAAQAAAAAQAAACAAAACgAAgAAAAAAAAAEAFAIAAAAIAECAgskdAAAAAAAAAAIAAYAAAABBVMAEg0KgCIsCAEIhAwggQACCgIAKBAEAAAQIAAACYIChAGACowGQAgBAAAAAAAAAAAAIAAAIAEIAAgAABAAAAABAAEABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAxAIEEAQAAIIACCgAAAAEAAAAAAAAABEAAQAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAABAgAABAAAAFAYgsAAAAAAAAAAAAAAAQAAIAAAABAA.YAAAAAAAEJTgAAAAAAAAAAAA; GUC=AQABCAFo-jNpI0IfzASA&s=AQAAAKMQiJnF&g=aPjnsw; cmp=t=1761149346&j=1&u=1---&v=102; PRF=t%3DBYND%252BWOLF%252BKLAR%26dock-collapsed%3Dtrue; _cb=DqHjtICXJ70UCbJGVZ; _chartbeat2=.1751028569278.1761151563669.0000000000000001.DqNHe0Clw2xkDtooPYGjJqaBIlLFP.2; A1S=d=AQABBNUAn2gCEBlZ68MYcYqLSZKWr3f-An0FEgABCAEz-mgjafU70CMA9qMCAAcI1QCfaHf-An0&S=AQAAAuLpqsKZ0ZKymfoHwORvTNg; EuConsent=CQWMLUAQWMLUAAOADBENB3FoAP_gAEPgACiQKZNB9G7WTWFjeTp2YPskOYwH0VBJ4MAwBgCBAUABzBIUIBwGRmAxJAyIICACGAIAIGBBIABlGABAQEAAIIAFAABIAEgAIBAAICAAAAAAAABACAAAAAAAAAAQgEAVMBQgmAYEBFoIQUhAggAAAQAAAAAEAIABAAQAAAAAQAAACAAAACgAAgAAAAAAAAAEAFAIAAAAIAECAgskdAAAAAAAAAAIAAYAAAABBVMAEg0KgCIsCAEIhAwggQACCgIAKBAEAAAQIAAACYIChAGACowGQAgBAAAAAAAAAAAAIAAAIAEIAAgAABAAAAABAAEABAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAxAIEEAQAAIIACCgAAAAEAAAAAAAAABEAAQAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAABAgAABAAAAFAYgsAAAAAAAAAAAAAAAQAAIAAAABAA.YAAAAAAABZTwAA; _cb_svref=https%3A%2F%2Fwww.google.com%2F; _SUPERFLY_lockout=1; _chartbeat4=t=C31rm9DT4kkaCZXPhVDHrwL1Bgtz9-&E=14&x=0&c=0.59&y=1352&w=1352",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "websocket",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}
sio = socketio.AsyncClient()
console = Console()


async def background():
    console.print("[green]Connected to server[/green]")
    # The string you provided
    input_string = (
        # "CgRRQlRTFZqZ7UEYsO3SxMFmKgNOWVEwCDgBRbSH98BIrKX5EmUgXB/AsAHGBdgBBA=="
        "CgNBVlkVSOEwQxiwpPzMwWYqA05ZUTAIOAFFSZ4CQUiKnFploJlVQdgBBA=="
    )
    console.print(f"[cyan]Input String:[/cyan] {input_string}")
    decode_and_print_protobuf(input_string)
    await asyncio.sleep(5)


async def main():
    try:
        console.print("[green]Connected to server[/green]")
        await sio.connect(url=url)
        # headers=headers, transports=["websocket"])
        console.print("[green]Connected to server[/green]")
        task = sio.start_background_task(background)
        await asyncio.gather(sio.wait(), task)
    except asyncio.CancelledError:
        await sio.disconnect()
        console.print("[red]Disconnected from server[/]")


if __name__ == "__main__":
    asyncio.run(main())
