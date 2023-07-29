import serial
import base64


def main(i = 0):
    print('connecting to serial port...')
    ser = serial.Serial('COM4')
    print('connected')
    print('read rom header')
    ser.write(b'header\n')
    raw_header = receive(ser)
    header = Header(raw_header)
    print(header)
    print('ROM header received')
    print('dump rom data')
    rom_data = dump_rom(ser, header)
    print('ROM data received')
    print('calc checksum')
    checksum = calc_checksum(rom_data)
    print(f'checksum: {checksum:04x}')
    print(f'header checksum: {header.checksum:04x}')
    if checksum != header.checksum:
        print('checksum mismatch')
        try:
            print('verify rom data')
            diff_chunks = verify_rom(ser, header, rom_data)
            print('fix rom data')
            rom_data = fix_rom(ser, header, rom_data, diff_chunks)
        except IOError as e:
            print(e)
    ser.close()
    print('writing rom data to file...')
    checksum = calc_checksum(rom_data)
    rom_name = header.title.strip().replace(" ", "_") + (f'_checksum_mismatch_{i}' if checksum != header.checksum else '')
    with open(f'{rom_name}.sfc', 'wb') as f:
        f.write(rom_data)
    print('done')
    if checksum != header.checksum:
        main(i + 1)


class Header:
    def __init__(self, data):
        try:
            self.title = data[0:20].decode('ascii')
        except UnicodeDecodeError:
            self.title = bytes([(i if i < 0x80 else 0x3f) for i in data[0:20]]).decode('ascii')
        self.rom_speed = 'Fast' if data[21] >> 4 & 1 else 'Slow'
        self.rom_type = 'HiROM' if data[21] & 1 else 'LoROM'
        self.rom_size = 1 << data[23]
        self.checksum = (data[29] << 8) + data[28]

    def __str__(self):
        return f'title: {self.title}\n' \
               f'rom speed: {self.rom_speed}\n' \
               f'rom type: {self.rom_type}\n' \
               f'rom size: {self.rom_size}KB\n' \
               f'checksum: {self.checksum:04x}'


def dump_rom(ser: serial, header: Header):
    rom_data = bytearray()
    next_addr = get_init_addr(header)
    whole_size = 0
    while True:
        print(f'dump ${next_addr:06x} ({whole_size // 1024}KB / {header.rom_size}KB)')
        next_addr, limit_size = get_next_addr_and_size(next_addr, header)
        if limit_size == 0:
            break
        size = min(limit_size, 1024)
        ser.write(f'dump 0x{next_addr:06x} {size}\n'.encode('ascii'))
        rom_data += receive(ser)
        next_addr += size
        whole_size += size
    return rom_data


def verify_rom(ser: serial, header: Header, rom_data: bytes):
    diff_chunks = []
    cart_addr = get_init_addr(header)
    file_addr = 0
    while True:
        print(f'verify ${cart_addr:06x} ({file_addr // 1024}KB / {header.rom_size}KB)')
        cart_addr, limit_size = get_next_addr_and_size(cart_addr, header)
        if limit_size == 0:
            break
        chunk_size = min(limit_size, 1024)
        ser.write(f'dump 0x{cart_addr:06x} {chunk_size}\n'.encode('ascii'))
        verify_chunk = receive(ser)
        if rom_data[file_addr:file_addr + chunk_size] != verify_chunk:
            error_length = 0
            for i in range(chunk_size):
                if rom_data[file_addr + i] != verify_chunk[i]:
                    error_length += 1
                    continue
                if error_length > 0:
                    diff_chunks.append((cart_addr + i - error_length, error_length))
                    error_length = 0
            if error_length > 0:
                diff_chunks.append((cart_addr + chunk_size - error_length, error_length))
        cart_addr += chunk_size
        file_addr += chunk_size

    if len(diff_chunks) == 0:
        raise IOError('verify failed')
    return diff_chunks

def fix_rom(ser: serial, header: Header, rom_data: bytes, diff_chunks: list[tuple[int, int]]):
    fix_rom_data = bytearray(rom_data)
    print(diff_chunks)
    for cart_addr, error_size in diff_chunks:
        file_addr = convert_addr_cart_to_file(cart_addr, header)
        reread_chunks = {}
        for i in range(5):
            ser.write(f'dump 0x{cart_addr:06x} {error_size}\n'.encode('ascii'))
            reread_chunk = receive(ser)
            reread_chunks[reread_chunk] = reread_chunks.get(reread_chunk, 0) + 1
        most_read_chunk = max(reread_chunks, key=reread_chunks.get)
        fix_rom_data[file_addr:file_addr + error_size] = most_read_chunk
    checksum = calc_checksum(fix_rom_data)
    if checksum != header.checksum:
        raise IOError('fix failed')
    print('fix success')
    return fix_rom_data


def convert_addr_cart_to_file(cart_addr, header):
    if header.rom_type == 'HiROM':
        return cart_addr & 0x3fffff
    else:
        # LoROM
        return ((cart_addr & 0xff0000) >> 1) + (cart_addr & 0x7fff)


def calc_checksum(data):
    checksum = 0
    for i in range(0, len(data)):
        checksum += data[i]
    return ~checksum & 0xffff


def receive(ser: serial):
    data = None
    while True:
        line = ser.readline()
        if line == b'done\r\n':
            break
        elif line.strip().isdigit():
            data = read_data(ser, line)
        else:
            print('client> ' + line.decode('ascii'), end='')
    return data


def read_data(ser, size):
    size = int(size)
    b64_data = ser.read(size + 1)  # converted \n -> \r\n in serial port
    return base64.b64decode(b64_data)


def get_next_addr_and_size(next_addr, header):
    if next_addr > 0xffffff:
        return 0, 0
    bank = next_addr >> 16
    start_bank = 0x00 if header.rom_type == 'LoROM' else 0xc0
    if bank >= start_bank + header.rom_size / 32:
        return 0, 0
    if header.rom_type == 'LoROM' and next_addr & 0xffff < 0x8000:
        next_addr += 0x8000
    size = 0xffff - (next_addr & 0xffff) + 1
    return next_addr, size


def get_init_addr(header):
    if header.rom_type == 'LoROM':
        return 0x008000
    else:
        return 0xc00000


if __name__ == '__main__':
    main()
