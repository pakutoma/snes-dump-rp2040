import sys

from machine import Pin, I2C

from dumper import Dumper
from mcp23017 import MCP23017


def main():
    i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=100000)
    print('i2c scan')
    addrs = i2c.scan()
    io = [MCP23017(i2c, addrs[0]), MCP23017(i2c, addrs[1])]
    print('pin init')
    dumper = Dumper(io)
    print('ready')
    while True:
        line = sys.stdin.readline()
        if line == 'header\n':
            dumper.read_header()
        elif line[0:4] == 'dump':
            dumper.dump(*line[5:].split(' '))
        elif line == 'exit\n':
            break
        else:
            print(f'unknown command: {line[:-1]}')


if __name__ == '__main__':
    main()
