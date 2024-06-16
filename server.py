import socket
import zlib
from datetime import datetime

def calculate_crc(data):
    return zlib.crc32(data) & 0xffffffff

def log(message):
    print(f"[{datetime.now()}] {message}")

def start_server(host='localhost', port=12345):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    log(f"Server started at {host}:{port}")

    expected_seq_num = 0
    file_data = b""

    while True:
        data, address = sock.recvfrom(1024)
        if not data:
            break

        seq_num = int.from_bytes(data[:4], 'big')
        received_crc = int.from_bytes(data[4:8], 'big')
        payload = data[8:]

        log(f"Received packet {seq_num} from {address}")

        if calculate_crc(payload) == received_crc:
            if seq_num == expected_seq_num:
                file_data += payload
                expected_seq_num += 1
                log(f"Packet {seq_num} received correctly.")
            ack = (seq_num + 1).to_bytes(4, 'big')
        else:
            log(f"Error detected in packet {seq_num}. Expected CRC: {received_crc}, Calculated CRC: {calculate_crc(payload)}")
            ack = expected_seq_num.to_bytes(4, 'big')
        
        sock.sendto(ack, address)
        log(f"Sent ACK {int.from_bytes(ack, 'big')} to {address}")

    with open('received_file.txt', 'wb') as f:
        f.write(file_data)

    log("File received and saved as received_file.txt")

if __name__ == "__main__":
    host = input("Enter the server host (default 'localhost'): ") or 'localhost'
    port = int(input("Enter the server port (default 12345): ") or 12345)
    start_server(host, port)
