import socketio
import requests
import base64
import time
import threading


sio = socketio.Client()
SLEEP_TIME = 0.04


class BitSet:
    def __init__(self, base64_string, count):
        binary_string = base64.b64decode(base64_string)
        self.bytes = bytearray(binary_string)
        self.check_count = count

    def get(self, index):
        byte_index = index // 8
        bit_offset = 7 - (index % 8)
        return (self.bytes[byte_index] & (1 << bit_offset)) != 0

    def set(self, index, value):
        if isinstance(value, bool):
            value = 1 if value else 0
        byte_index = index // 8
        bit_offset = 7 - (index % 8)
        current = self.bytes[byte_index] & (1 << bit_offset)
        if value:
            self.bytes[byte_index] |= 1 << bit_offset
            if current == 0:
                self.check_count += 1
        else:
            self.bytes[byte_index] &= ~(1 << bit_offset)
            if current != 0:
                self.check_count -= 1


headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://onemillioncheckboxes.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 '
                  'Safari/537.36',
    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
res = requests.get('https://onemillioncheckboxes.com/api/initial-state', headers=headers).json()
bitset = BitSet(res.get('full_state'), res.get('count'))


def uncheck_100():
    while True:
        for i in range(0, 600):
            if bitset.get(i):
                time.sleep(SLEEP_TIME)
                sio.emit('toggle_bit', {'index': i})
                bitset.set(i, False)
                print('first 100 at bay',  i)


def uncheck_everything():
    while True:
        for i in range(100000, 999999):
            if bitset.get(i):
                time.sleep(SLEEP_TIME)
                sio.emit('toggle_bit', {'index': i})
                bitset.set(i, False)
                print('unchecked box', i)
        print('done')


@sio.event
def connect():
    threading.Thread(target=uncheck_100).start()
    threading.Thread(target=uncheck_everything).start()


@sio.event
def connect_error(data):
    print(f"Connection failed: {data}")


@sio.event
def disconnect():
    print("Disconnected from the server")


@sio.on('batched_bit_toggles')
def on_message(data):
    true_changes = data[0]
    false_changes = data[1]
    for i in true_changes:
        bitset.set(i, True)
    for i in false_changes:
        bitset.set(i, False)


@sio.on('full_state')
def on_message(data):
    print(f"updating full state")
    binary_string = base64.b64decode(data['full_state'])
    byts = bytearray(binary_string)
    bitset.bytes = byts


if __name__ == "__main__":
    sio.connect('https://onemillioncheckboxes.com', transports='websocket')
    sio.wait()
