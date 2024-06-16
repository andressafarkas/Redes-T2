import socket
import zlib
import time
from datetime import datetime

def calculate_crc(data):
    return zlib.crc32(data) & 0xffffffff

def log(message):
    print(f"[{datetime.now()}] {message}")

def send_file(file_path, server_address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    with open(file_path, 'rb') as f:
        seq_num = 0
        while True:
            chunk = f.read(10)
            if not chunk:
                break

            crc = calculate_crc(chunk)
            packet = seq_num.to_bytes(4, 'big') + crc.to_bytes(4, 'big') + chunk
            log(f"Sending packet {seq_num} to {server_address}")
            sock.sendto(packet, server_address)

            start_time = datetime.now()

            while True:
                try:
                    sock.settimeout(1.0)
                    ack, _ = sock.recvfrom(1024)
                    ack_num = int.from_bytes(ack, 'big')
                    if ack_num == seq_num + 1:
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        log(f"Received ACK {ack_num} in {duration:.4f} seconds")
                        break
                except socket.timeout:
                    log(f"Timeout, resending packet {seq_num}")
                    sock.sendto(packet, server_address)
            
            seq_num += 1
            time.sleep(0.5)  # Sleep to visualize packet sending

    sock.close()
    log("File sent successfully.")

if __name__ == "__main__":
    file_path = input("Enter the file path to send: ")
    host = input("Enter the server host (default 'localhost'): ") or 'localhost'
    port = int(input("Enter the server port (default 12345): ") or 12345)
    send_file(file_path, (host, port))
