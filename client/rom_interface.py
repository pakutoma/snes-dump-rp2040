import time


def set_address(io, addr, old_addr=None):
    # A23-A0
    ports = [io[1].porta, io[0].portb, io[0].porta]

    return_addr = addr
    for port in reversed(ports):
        if old_addr is not None:
            if (addr & 0xff) == (old_addr & 0xff):
                addr >>= 8
                old_addr >>= 8
                continue
            else:
                old_addr >>= 8
        port.gpio = addr & 0xff
        addr >>= 8
    return return_addr


def init_connector(io):
    # set zero to all pins
    for chip in range(2):
        for pin in range(16):
            write(io, chip, pin, 0)

    # assign input to D7-D0
    pin_assigns = [
        (1, 15), (1, 14), (1, 13), (1, 12), (1, 11), (1, 10), (1, 9), (1, 8)
    ]
    for data_pin in pin_assigns:
        init_input(io, data_pin[0], data_pin[1])


def read_byte(io):
    def _read_byte():
        # D7-D0
        return io[1].portb.gpio

    return _retry(_read_byte)


def read(io, chip, pin):
    def _read():
        return io[chip][pin].value()

    return _retry(_read)


def write(io, chip, pin, value):
    def _write():
        io[chip][pin].output(value)

    return _retry(_write)


def init_input(io, chip, pin):
    def _init_input():
        io[chip][pin].input()

    return _retry(_init_input)


def _retry(func):
    retry = 0
    while retry < 10:
        try:
            return func()
        except OSError:
            retry += 1
            time.sleep_ms(1)
            print('retry')
