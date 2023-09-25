
import base64
import pathlib
from typing import Union

from nacl.public import PrivateKey, PublicKey
import typer


_app = typer.Typer()


def text_to_bytes(text: Union[str, bytes]) -> bytes:
    if not isinstance(text, bytes):
        text = text.encode()
    if text.startswith(b'base64:'):
        decoded = base64.decodebytes(text.replace(b'base64:', b''))
        return decoded
    return text


def privkey(text: Union[str, bytes, pathlib.Path]) -> PrivateKey:
    if isinstance(text, pathlib.Path):
        text = text.read_bytes()
    return PrivateKey(text_to_bytes(text))


def pubkey(text: Union[str, bytes]) -> PublicKey:
    return PublicKey(text_to_bytes(text))


@_app.command()
def _generate_keypair(output_path: pathlib.Path = typer.Option('./key')):
    keypair = PrivateKey.generate()
    privkey_bytes = keypair.encode()
    privkey_base64 = base64.encodebytes(privkey_bytes)
    output_path.write_bytes(b'base64:'+privkey_base64)
    print(f'Saved base64 encoded privkey to {output_path}')
    pubkey_bytes = keypair.public_key.encode()
    pubkey_base64 = base64.encodebytes(pubkey_bytes)
    pubkey_path = output_path.with_suffix('.pub')
    pubkey_path.write_bytes(b'base64:'+pubkey_base64)
    print(f'Saved base64 encoded pubkey to {pubkey_path}: '
          f'{pubkey_base64.decode()}')