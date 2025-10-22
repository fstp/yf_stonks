#!/usr/bin/env -S uv run --script
# vim: ft=python
# /// script
# dependencies = [
#   "rich",
#   "getch",
#   "python-socketio[asyncio_client]",
#   "pynacl",
# ]
# ///
import asyncio
import base64
import json
import logging
import zlib
from datetime import datetime
from typing import Any, Dict

import getch
import socketio
from nacl.secret import SecretBox
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.logging import RichHandler
from rich.prompt import Prompt
from rich.table import Table
from rich.traceback import install

install(show_locals=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%X",
    handlers=[RichHandler(markup=True, rich_tracebacks=True)],
)
log = logging.getLogger("rich_gui")
console = Console()

state: Dict[str, Dict[str, Any]] = {}
persistent_state: Dict[str, Dict[str, Any]] = {}
symbols_to_subscribe = ["spx:ind"]

headers = {
    "Host": "live.tradingeconomics.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": "https://tradingeconomics.com",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Referer": "https://tradingeconomics.com/",
    "Cookie": "AWSALB=M9i/Ouy2UJgKBqF5jkhrK5rNJnzFUsptSlPcOPOFqxOQD60VmEl1BK5jejTf4/yUTlem2HbLEfjWzKRCjvTWnsRwHwOuRvoX37ts9N3g1WC1y5eV4gW6TfQFAgs7; AWSALBCORS=M9i/Ouy2UJgKBqF5jkhrK5rNJnzFUsptSlPcOPOFqxOQD60VmEl1BK5jejTf4/yUTlem2HbLEfjWzKRCjvTWnsRwHwOuRvoX37ts9N3g1WC1y5eV4gW6TfQFAgs7",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "TE": "trailers",
}

url = "https://live.tradingeconomics.com/socket.io/?key=rain&url=%2Fsweden%2Fstock-market&t=POQpB1c"
sio = socketio.AsyncClient()

TEdecryptk = "j9ONifjoKzxt7kmfYTdKK/5vve0b9Y1UCj/n50jr8d8="
TEdecryptn = "Ipp9HNSfVBUntqFK7PrtofYaOPV312xy"


def _base64_to_bytes(base64_string):
    """Converts a Base64 string to a bytes object."""
    return base64.b64decode(base64_string)


def decrypt_base64_message(ciphertext: str) -> Dict[str, Any]:
    """Decrypts a ciphertext base64 string using the provided key and nonce."""
    key = _base64_to_bytes(TEdecryptk)
    nonce = _base64_to_bytes(TEdecryptn)
    box = SecretBox(key)
    decrypted_plaintext = box.decrypt(base64.b64decode(ciphertext), nonce)
    decrypted_plaintext = zlib.decompress(decrypted_plaintext).decode("utf-8")
    return json.loads(decrypted_plaintext)


def decrypt_binary_message(ciphertext: bytes) -> Dict[str, Any]:
    """Decrypts a ciphertext in bytes using the provided key and nonce."""
    key = _base64_to_bytes(TEdecryptk)
    nonce = _base64_to_bytes(TEdecryptn)
    box = SecretBox(key)
    decrypted_plaintext = box.decrypt(ciphertext, nonce)
    decrypted_plaintext = zlib.decompress(decrypted_plaintext).decode("utf-8")
    return json.loads(decrypted_plaintext)


def timestamp_to_datetime(ts: float) -> datetime:
    return datetime.fromtimestamp(ts / 1000).replace(microsecond=0)


def format_pch(pch: float) -> str:
    """
    Format the percentage change (pch) value with color coding.

    Args:
        pch (float): The percentage change value to be formatted.

    Returns:
        str: The formatted percentage change value wrapped in color tags.
             If the value is non-negative, it is wrapped in green color tags.
             If the value is negative, it is wrapped in red color tags.
    """
    if pch >= 0.0:
        return f"[green]{pch}%[/]"
    else:
        return f"[red]{pch}%[/]"


def update_persistent_state(symbol: str, pch: float) -> None:
    """
    If symbol is in persistent state then set min_pch and max_pch
    """
    global persistent_state

    if symbol in persistent_state:
        if pch > persistent_state[symbol]["max_pch"]:
            persistent_state[symbol]["max_pch"] = pch
        if pch < persistent_state[symbol]["min_pch"]:
            persistent_state[symbol]["min_pch"] = pch
    else:
        persistent_state[symbol] = {"max_pch": pch, "min_pch": pch}


@sio.on("tick")  # type:ignore
async def handle_tick(data: bytes) -> None:
    """
    Event handler for the "tick" event.

    This function is triggered whenever a "tick" event is received. It processes the incoming data,
    decrypts it, converts the timestamps to human-readable datetime format, and updates the global state.

    Args:
        data (bytes): The encrypted binary message received from the "tick" event.
    """
    global state
    decrypted_data = decrypt_binary_message(data)
    decrypted_data["dt"] = timestamp_to_datetime(decrypted_data["dt"])
    decrypted_data["odt"] = timestamp_to_datetime(decrypted_data["odt"])
    state[decrypted_data["s"].lower()] = decrypted_data
    update_persistent_state(symbol=decrypted_data["s"], pch=decrypted_data["pch"])


@sio.event
async def connect() -> None:
    log.info("[green]Connected to server[/]")
    log.info(f"My sid is [bold]{sio.sid}[/]")
    await sio.emit("subscribe", {"s": symbols_to_subscribe})


@sio.event
async def disconnect():
    log.info("[red]Disconnected from server[/]")


def create_layout() -> Layout:
    """
    Create and return a root layout with two split rows.

    The root layout is split into two sub-layouts: 'left' and 'right'.

    Returns:
        Layout: The root layout with 'left' and 'right' sub-layouts.
    """
    layout = Layout(name="root")
    layout["root"].split_column(
        Layout(name="0"),
    )
    layout["root"]["0"].split_row(
        Layout(name="00"), Layout(name="01"), Layout(name="02")
    )
    return layout


def create_table(symbol: str, width=30) -> Table:
    """
    Create a table with symbol data.

    This function creates a table with two columns: 'Key' and 'Value'.
    It populates the table with key-value pairs which contains all
    received symbol data.

    Args:
        symbol (str): Symbol to display.

    Returns:
        Table: A table object populated with the symbol data.
    """
    global state
    if symbol in state:
        table = Table(title=symbol)

        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        for key, value in state[symbol].items():
            if key == "pch":
                value = format_pch(value)
            table.add_row(key, str(value))

        for key, value in persistent_state.get(symbol, {}).items():
            if key == "max_pch" or key == "min_pch":
                value = format_pch(value)
            table.add_row(key, str(value))

        table.width = width
        return table

    # If no symbol data is found
    return Table(title=symbol)


async def background():
    global console
    layout = create_layout()
    with Live(layout, console=console, screen=True, auto_refresh=False) as live:
        while True:
            size = 35
            height = 16
            layout["0"].size = height
            layout["0"]["00"].size = size
            layout["0"]["01"].size = size
            layout["0"]["02"].size = size
            layout["0"]["00"].update(create_table("spx:ind", width=size))

            live.update(layout, refresh=True)
            await asyncio.sleep(0.2)


async def main():
    try:
        await sio.connect(
            url=url,
            headers=headers,
        )
        task = sio.start_background_task(background)
        await asyncio.gather(
            sio.wait(),
            task,
        )
    except asyncio.CancelledError:
        await sio.disconnect()
        console.print("[red]Disconnected from server[/]")


if __name__ == "__main__":
    asyncio.run(main())
    log.info(state)
    # log.info("[bold green]Rich GUI Script Running[/bold green]")

    # while True:
    #     name = Prompt.ask("What is your name?")
    #     log.info(f"Hello, {name}!")

    #     log.info("Press ESC to exit, or any other key to continue.")
    #     key = getch.getch()
    #     if ord(key) == 27:  # 27 is the ASCII code for ESC
    #         break
