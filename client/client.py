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
    
    start_time = datetime.now()
    total_packets_sent = 0
    total_retransmissions = 0

    with open(file_path, 'rb') as f:
        seq_num = 0
        while True:
            chunk = f.read(10)
            if not chunk:
                break

            if len(chunk) < 10:
                chunk = chunk.ljust(10, b'\0')  # Pad the last chunk to ensure it is 10 bytes

            crc = calculate_crc(chunk)
            packet = seq_num.to_bytes(4, 'big') + crc.to_bytes(4, 'big') + chunk
            log(f"Sending packet {seq_num} to {server_address}")
            sock.sendto(packet, server_address)
            total_packets_sent += 1

            start_packet_time = datetime.now()

            while True:
                try:
                    sock.settimeout(1.0)
                    ack, _ = sock.recvfrom(1024)
                    ack_num = int.from_bytes(ack, 'big')
                    if ack_num == seq_num + 1:
                        end_packet_time = datetime.now()
                        duration = (end_packet_time - start_packet_time).total_seconds()
                        log(f"Received ACK {ack_num} in {duration:.4f} seconds")
                        break
                except socket.timeout:
                    log(f"Timeout, resending packet {seq_num}")
                    sock.sendto(packet, server_address)
                    total_retransmissions += 1
            
            seq_num += 1
            time.sleep(0.5)  # Sleep to visualize packet sending

    # Send termination packet
    termination_packet = b'TERMINATION'
    log(f"Sending termination packet to {server_address}")
    sock.sendto(termination_packet, server_address)
    sock.close()

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    log("File sent successfully.")
    log(f"Total packets sent: {total_packets_sent}")
    log(f"Total retransmissions: {total_retransmissions}")
    log(f"Total duration: {total_duration:.4f} seconds")

if __name__ == "__main__":
    file_path = input("Enter the file path to send: ")
    host = input("Enter the server host (default 'localhost'): ") or 'localhost'
    port = int(input("Enter the server port (default 12345): ") or 12345)
    send_file(file_path, (host, port))
