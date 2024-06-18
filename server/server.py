import random
import socket
import zlib
from datetime import datetime
import time

def calculate_crc(data):
    return zlib.crc32(data) & 0xffffffff

def log(message):
    print(f"[{datetime.now()}] {message}")

def start_server(host='localhost', port=12345, error_rate=0.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permite reuso de endereço socket
    sock.bind((host, port))
    log(f"Server started at {host}:{port}")

    expected_seq_num = 0
    file_data = b""
    total_packets_received = 0
    total_packets_with_error = 0
    start_time = datetime.now()

    while True:
        data, address = sock.recvfrom(1024)
        # Estabelecimento de conexão
        if data == b'SYN':
            log(f"Received SYN from {address}, sending SYN_ACK")
            sock.sendto(b'SYN_ACK', address)
            while True:
                ack, _ = sock.recvfrom(1024)
                if ack == b'ACK':
                    log(f"Received ACK from {address}")
                    break
            continue
        # Encerramento da conexão
        if data == b'FIN':
            log(f"Received FIN from {address}, sending ACK")
            sock.sendto(b'ACK', address)
            log(f"Sending FIN + ACK to {address}")
            sock.sendto(b'FIN_ACK', address)
            while True:
                ack, _ = sock.recvfrom(1024)
                if ack == b'ACK':
                    log(f"Received ACK from {address}")
                    break
            break

        if not data:
            continue

        seq_num = int.from_bytes(data[:4], 'big')
        received_crc = int.from_bytes(data[4:8], 'big')
        payload = data[8:]

        total_packets_received += 1
        log(f"Received packet {seq_num} from {address}")

        # Calcula crc presente no pacote recebido
        if calculate_crc(payload) == received_crc:
            # verifica se sequencia recebida é a esperada
            if seq_num == expected_seq_num:
                rnd = random.random()
                if rnd > error_rate: 
                    expected_seq_num += 1
                    log(f"Packet {seq_num} received correctly.")
                    ack = (seq_num + 1).to_bytes(4, 'big')
                    file_data += payload
                    sock.sendto(ack, address)
                    log(f"Sent ACK {int.from_bytes(ack, 'big')} to {address}")
                else:
                    log(f"Simulated error, ACK {int.from_bytes(ack, 'big')} not sent.")
        else:
            total_packets_with_error += 1
            log(f"Error detected in packet {seq_num}. Expected CRC: {received_crc}, Calculated CRC: {calculate_crc(payload)}")
            ack = expected_seq_num.to.bytes(4, 'big')
        
        time.sleep(0.5)  # Sleep para visualizar recebimento

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    # Remove padding
    file_data = file_data.rstrip(b'\0')

    with open('received_file.txt', 'wb') as f:
        f.write(file_data)

    log("File received and saved as received_file.txt")
    log(f"Total packets received: {total_packets_received}")
    log(f"Total packets with error: {total_packets_with_error}")
    log(f"Total duration: {total_duration:.4f} seconds")

if __name__ == "__main__":
    host = input("Enter the server host (default 'localhost'): ") or 'localhost'
    port = int(input("Enter the server port (default 12345): ") or 12345)
    error_rate = float(input("Enter the error rate (0.0 - 1.0): ") or 0.0)
    start_server(host, port, error_rate)
