import socket
import zlib
import time

def calculate_crc(data):
    return zlib.crc32(data) & 0xffffffff

def send_file(file_path, server_address=('localhost', 12345)):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    with open(file_path, 'rb') as f:
        seq_num = 0
        while True:
            chunk = f.read(10)
            if not chunk:
                break

            crc = calculate_crc(chunk)
            packet = seq_num.to_bytes(4, 'big') + crc.to_bytes(4, 'big') + chunk
            sock.sendto(packet, server_address)

            while True:
                try:
                    sock.settimeout(1.0)
                    ack, _ = sock.recvfrom(1024)
                    ack_num = int.from_bytes(ack, 'big')
                    if ack_num == seq_num + 1:
                        break
                except socket.timeout:
                    sock.sendto(packet, server_address)
            
            seq_num += 1

    sock.close()
    print("File sent successfully.")

if __name__ == "__main__":
    file_path = "test_file.txt"  # Path to the file you want to send
    send_file(file_path)
