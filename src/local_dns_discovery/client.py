import os
import socket


def client_main():
    if not os.getenv("SERVER_IP"):
        print('SERVER_IP not set, unable to report.')
        exit(1)

    hostname = socket.gethostname()
    server_addr = (os.getenv("SERVER_IP"), int(os.getenv("SERVER_PORT", "3671")))

    print('reporting...')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.sendto(hostname.encode(), server_addr)
    s.close()
