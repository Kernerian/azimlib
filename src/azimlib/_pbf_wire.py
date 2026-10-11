"""Independent bounded protobuf wire decoding, without generated schemas."""
from array import array
from ._contracts import STREAM_WORKING_BUDGET


def varint(data, offset):
    value = 0
    for index in range(10):
        if offset >= len(data):
            raise ValueError('Truncated PBF varint')
        byte = data[offset]; offset += 1
        if index == 9 and byte > 1:
            raise ValueError('PBF varint overflows uint64')
        value |= (byte & 127) << (7 * index)
        if byte < 128:
            return value, offset
    raise ValueError('Invalid PBF varint')


class Budget:
    def __init__(self, limit=STREAM_WORKING_BUDGET.max_items):
        self.left = limit
        self.max_fields = 100_000

    def take(self, count=1):
        self.left -= count
        if self.left < 0:
            raise ValueError('PBF block exceeds decoded item budget')

def fields(data, budget):
    data = memoryview(data); offset = 0; result = {}; count = 0
    while offset < len(data):
        count += 1
        if count > budget.max_fields:
            raise ValueError('PBF message exceeds structural field budget')
        budget.take()
        key, offset = varint(data, offset)
        number, wire = key >> 3, key & 7
        if not 0 < number < 2**29:
            raise ValueError('Invalid PBF field number')
        if wire == 0:
            value, offset = varint(data, offset)
        elif wire in (1, 2, 5):
            if wire == 2:
                size, offset = varint(data, offset)
            else:
                size = 8 if wire == 1 else 4
            end = offset + size
            if end > len(data):
                raise ValueError('Truncated PBF field')
            value = data[offset:end]; offset = end
        else:
            raise ValueError('Unsupported PBF protobuf group/wire type')
        result.setdefault(number, []).append((wire, value))
    return result


_ABSENT = object()


def one(message, number, wire, default=_ABSENT):
    items = message.get(number, ())
    if not items:
        if default is _ABSENT:
            raise ValueError(f'Missing required PBF field {number}')
        return default
    if len(items) != 1 or items[0][0] != wire:
        raise ValueError(f'Duplicate or invalid PBF field {number}')
    return items[0][1]


def chunks(message, number):
    for wire, value in message.get(number, ()):
        if wire != 2:
            raise ValueError('PBF message/string has wrong wire type')
        yield value


def signed(value):
    return value - 2**64 if value >= 2**63 else value


def zigzag(value):
    return (value >> 1) ^ -(value & 1)


def int32(value):
    value = signed(value)
    if not -(2**31) <= value < 2**31:
        raise ValueError('PBF int32 overflow')
    return value


def numbers(message, number, budget, decode=lambda x: x):
    result = array('q')
    for wire, value in message.get(number, ()):
        if wire == 0:
            budget.take(); values = (value,)
        elif wire == 2:
            def unpack(data):
                offset = 0
                while offset < len(data):
                    budget.take()
                    item, offset = varint(data, offset)
                    yield item
            values = unpack(value)
        else:
            raise ValueError('Invalid packed PBF field')
        for item in values:
            decoded = decode(item)
            if not -(2**63) <= decoded < 2**63:
                raise ValueError('PBF integer overflow')
            result.append(decoded)
    return result


def deltas(values):
    previous = 0
    for index, value in enumerate(values):
        previous += value
        if not -(2**63) <= previous < 2**63:
            raise ValueError('PBF delta overflows int64')
        values[index] = previous
    return values


def text(value):
    try:
        return bytes(value).decode('utf8')
    except UnicodeError as exc:
        raise ValueError('Invalid PBF UTF-8 string') from exc
