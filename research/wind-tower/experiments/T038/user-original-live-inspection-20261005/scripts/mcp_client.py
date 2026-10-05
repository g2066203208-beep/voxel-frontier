"""Client for the installed Abaqus MCP GUI bridge, not a new server."""
import argparse
import datetime
import json
from pathlib import Path
import socket
import sys
import uuid


def request(method, params, tag):
    payload = {'id': 'codex-' + uuid.uuid4().hex, 'method': method, 'params': params}
    with socket.create_connection(('127.0.0.1', 48152), timeout=5) as sock:
        sock.settimeout(float(params.get('timeout', 45)) + 10)
        sock.sendall((json.dumps(payload, ensure_ascii=False) + '\n').encode('utf-8'))
        data = b''
        while b'\n' not in data:
            chunk = sock.recv(65536)
            if not chunk:
                raise RuntimeError('Bridge disconnected before response')
            data += chunk
    reply = json.loads(data.split(b'\n', 1)[0])
    record = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'request': payload, 'response': reply}
    target = Path(__file__).parent / (tag + '.json')
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    if not reply.get('ok'):
        raise RuntimeError(json.dumps(reply, ensure_ascii=False))
    result = reply.get('result')
    if method == 'execute' and isinstance(result, dict) and not result.get('ok'):
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('script')
    parser.add_argument('--tag', required=True)
    parser.add_argument('--timeout', type=float, default=45)
    args = parser.parse_args()
    code = Path(args.script).read_text(encoding='utf-8-sig')
    print(json.dumps(request('execute', {'code': code, 'timeout': args.timeout}, args.tag), ensure_ascii=False, indent=2))
