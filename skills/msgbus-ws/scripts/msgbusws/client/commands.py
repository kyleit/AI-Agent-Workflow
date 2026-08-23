"""Subcommand use-cases. Each function is a thin orchestration over the adapters."""
from __future__ import annotations

import json

from .config import ClientConfig, build_cipher, save_profile
from .rest_client import RestClient
from .tus_client import RangeDownloader, TusUploader
from .ws_client import WsClient


def _format(record: dict, cipher) -> str:
    seq = record.get("seq")
    ts = record.get("ts", "")
    frm = record.get("from", "")
    to = record.get("to")
    text = cipher.decrypt(record.get("text", ""))
    arrow = f" → {to}" if to else ""
    return f"#{seq} [{ts}] {frm}{arrow}: {text}"


def cmd_init(config: ClientConfig, args) -> None:
    """Save a connection profile so later sessions just run `join`/`listen`."""
    path = save_profile(config, save_sender=bool(getattr(args, "sender", None)))
    print(f"[msgbus] profile saved -> {path}")
    print(f"[msgbus] host={config.host} port={config.port} tls={config.secure} "
          f"e2ee={'on' if config.e2ee_key else 'off'}")
    print("[msgbus] now just run:  msgbus_client.py join")


def cmd_health(config: ClientConfig, args) -> None:
    print(json.dumps(RestClient(config).health(), ensure_ascii=False))


def cmd_send(config: ClientConfig, args) -> None:
    cipher = build_cipher(config)
    result = RestClient(config).send(cipher.encrypt(args.text), args.to)
    print(json.dumps(result, ensure_ascii=False))


def cmd_recv(config: ClientConfig, args) -> None:
    cipher = build_cipher(config)
    for record in RestClient(config).recv(args.since):
        print(_format(record, cipher))


def cmd_list(config: ClientConfig, args) -> None:
    for meta in RestClient(config).list_files():
        print(f"{meta['name']}\t{meta['size']}\t{meta['ts']}")


def cmd_upload(config: ClientConfig, args) -> None:
    print(json.dumps(TusUploader(config).upload(args.path, args.to), ensure_ascii=False))


def cmd_download(config: ClientConfig, args) -> None:
    print(json.dumps(RangeDownloader(config).download(args.name, args.out), ensure_ascii=False))


def cmd_listen(config: ClientConfig, args) -> None:
    cipher = build_cipher(config)
    print(f"[msgbus] {config.sender} listening (WS) since={args.since} …", flush=True)
    try:  # plaintext presence greeting so peers know who joined
        RestClient(config).send(f"{config.sender} đã vào bus", None)
    except OSError:
        pass

    def on_message(record: dict) -> bool:
        print(_format(record, cipher), flush=True)
        return False

    WsClient(config).listen(on_message, since=args.since)


def cmd_ws_send(config: ClientConfig, args) -> None:
    cipher = build_cipher(config)
    WsClient(config).send_text(cipher.encrypt(args.text), args.to)
    print(json.dumps({"status": "sent", "via": "ws", "to": args.to}, ensure_ascii=False))
