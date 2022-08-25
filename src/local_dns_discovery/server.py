import os
import socket
import subprocess


def add_host(ip, name):
    with open('/etc/pihole/custom.list') as f:
        content = f.read()

    has_merged = False
    has_changed = False
    result = []

    for line in content.split('\n'):
        if line.startswith('#'):
            result.append(line)
            continue

        if not line:
            result.append('')
            continue

        parts = line.split()
        if len(parts) < 2:
            result.append(line)
            continue

        if ':' in parts[0]:  # skip ipv6
            result.append(line)
            continue

        if parts[0].startswith('127'):  # skip 127.0.0.1 loopback
            result.append(line)
            continue

        current_ip = parts[0]
        current_hosts = parts[1:]

        if current_ip == ip:
            has_merged = True

            if name in current_hosts:
                result.append(line)
                continue
            else:
                current_hosts.append(name)
                has_changed = True
        else:
            if name in current_hosts:
                current_hosts.remove(name)
                has_changed = True
            else:
                result.append(line)
                continue

        if not current_hosts:
            continue

        result.append("{}\t{}".format(current_ip, '\t'.join(current_hosts)))
        has_changed = True

    if not has_merged:
        result.append("{}\t{}".format(ip, name))
        has_changed = True

    if not has_changed:
        return False

    with open('/etc/pihole/custom.list', 'w') as f:
        f.write('\n'.join(result))

    return True


def server_main():
    listen_port = int(os.getenv("LISTEN_PORT", "3671"))
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', listen_port))

    print('Server started, listening on port {}...'.format(listen_port))

    while True:
        data, address = s.recvfrom(4096)

        host_ip = address[0]
        host_name = data.decode()

        print('Adding host: {} ({})'.format(host_name, host_ip))
        if add_host(host_ip, host_name):
            print('reloading pihole...')
            subprocess.check_call(["pihole", "restartdns", "reload-lists"])
