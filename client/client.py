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

    # Estabelecimento de conexão
    log("Sending SYN to establish connection")
    sock.sendto(b'SYN', server_address)
    
    while True:
        try:
            sock.settimeout(1.0)
            syn_ack, _ = sock.recvfrom(1024)
            if syn_ack == b'SYN_ACK':
                log("Received SYN_ACK.")
                log("Sending ACK to establish connection")
                sock.sendto(b'ACK', server_address)
                break
        except socket.timeout:
            log("Timeout, resending SYN")
            sock.sendto(b'SYN', server_address)
    
    start_time = datetime.now()
    total_packets_sent = 0
    total_retransmissions = 0

    # Controle de congestionamento
    cwnd = 1  # Tamanho da janela de congestionamento (inicialmente 1 pacote)
    ssthresh = 16  # Limite do Slow Start para transição para Congestion Avoidance (valor arbitrário)
    slow_start = True  # Indicador de Slow Start

    with open(file_path, 'rb') as f:
        seq_num = 0
        packets = []
        while True:
            chunk = f.read(10)
            if not chunk:
                break

            if len(chunk) < 10:
                chunk = chunk.ljust(10, b'\0')  # Pad the last chunk to ensure it is 10 bytes

            crc = calculate_crc(chunk)
            packet = seq_num.to_bytes(4, 'big') + crc.to_bytes(4, 'big') + chunk
            packets.append(packet)
            seq_num += 1

    next_seq_num = 0
    acked_seq_num = 0

    while next_seq_num < len(packets):
        count = 0

        for _ in range(cwnd):
            if next_seq_num >= len(packets):
                break
            log(f"Sending packet {next_seq_num} to {server_address}")
            sock.sendto(packets[next_seq_num], server_address)
            total_packets_sent += 1
            next_seq_num += 1
            count += 1

        if slow_start:
            cwnd *= 2  # Crescimento exponencial
            if cwnd >= ssthresh:
                slow_start = False
        else:
            cwnd += 1  # Crescimento linear (Congestion Avoidance)

        print("PACKETS ENVIADOS --------------------")
        print(count)
        print("-------------------------------------")

        start_packet_time = datetime.now()

        while acked_seq_num < next_seq_num:
            try:
                sock.settimeout(1.0)
                ack, _ = sock.recvfrom(1024)
                ack_num_rcv = int.from_bytes(ack, 'big')
                if ack_num_rcv > acked_seq_num:
                    end_packet_time = datetime.now()
                    duration = (end_packet_time - start_packet_time).total_seconds()
                    log(f"Received ACK {ack_num_rcv} in {duration:.4f} seconds")
                    acked_seq_num = ack_num_rcv
            except socket.timeout:
                log(f"Timeout, resending packets from {acked_seq_num} to {next_seq_num}")
                total_retransmissions += 1
                next_seq_num = acked_seq_num  # Reiniciar envio a partir do último ACK confirmado
                cwnd = 1  # Resetar janela de congestionamento
                slow_start = True
                break
            
            time.sleep(0.5)  # Sleep to visualize packet sending

    # Encerramento da conexão
    log("Sending FIN to terminate connection")
    sock.sendto(b'FIN', server_address)
    
    while True:
        try:
            sock.settimeout(1.0)
            fin_ack, _ = sock.recvfrom(1024)
            if fin_ack == b'ACK':
                log("Received ACK.")
                continue
            if fin_ack == b'FIN_ACK':
                log("Received FIN + ACK.")
                log("Sending ACK to terminate connection.")
                sock.sendto(b'ACK', server_address)
                break
        except socket.timeout:
            log("Timeout, resending FIN")
            sock.sendto(b'FIN', server_address)

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
