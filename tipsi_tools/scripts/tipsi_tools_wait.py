import argparse

from tipsi_tools.unix import wait_no_socket, wait_socket

parser = argparse.ArgumentParser(description='Wait for socket')

parser.add_argument('-t', '--timeout', type=int, default=120)
parser.add_argument('-n', '--no-socket', action='store_true', default=False)
parser.add_argument('host', type=str)
parser.add_argument('port', type=int)


def main():
    args = parser.parse_args()
    print(args)
    f = wait_no_socket if args.no_socket else wait_socket
    if not f(args.host, args.port, args.timeout):
        print('Timeout')
        exit(1)
    else:
        print('Ok')


if __name__ == '__main__':
    main()
