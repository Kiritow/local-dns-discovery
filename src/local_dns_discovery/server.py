import os
import socket
import subprocess
from threading import Timer, Event
import traceback


def add_host(ip, name):
    with open('/etc/pihole/custom.list') as f:
        content = f.read()

    has_merged = False
    result = []

    for line in content.split('\n'):
        if line.startswith('#'):
            result.append(line)
            continue

        if not line:
            # remove empty line
            continue

        parts = line.split()
        if len(parts) != 2:
            result.append(line)
            continue

        if ':' in parts[0]:  # skip ipv6
            result.append(line)
            continue

        current_ip = parts[0]
        current_host = parts[1]

        if current_ip == ip and name == current_host:
            has_merged = True
            result.append(line)
            continue

        if name == current_host:
            # remove current line by not adding into result
            continue

        # other hosts with same ip
        result.append(line)

    if not has_merged:
        result.append("{} {}".format(ip, name))

    new_content = '\n'.join(result)
    if new_content == content:
        return False

    with open('/etc/pihole/custom.list', 'w') as f:
        f.write('\n'.join(result))

    return True


def do_restart_pihole():
    try:
        subprocess.check_call(["pihole", "restartdns"])
    except Exception:
        print(traceback.format_exc())


def server_main():
    listen_port = int(os.getenv("LISTEN_PORT", "3671"))
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', listen_port))

    print('Server started, listening on port {}...'.format(listen_port))

    e = Event()

    def restart_pihole():
        if e.is_set():
            e.clear()
            do_restart_pihole()
        Timer(60, restart_pihole).start()

    Timer(60, restart_pihole).start()

    while True:
        data, address = s.recvfrom(4096)

        host_ip = address[0]
        host_name = data.decode()

        print('Adding host: {} ({})'.format(host_name, host_ip))
        if add_host(host_ip, host_name):
            print('reloading pihole...')
            subprocess.check_call(["pihole", "restartdns", "reload-lists"])
            e.set()
