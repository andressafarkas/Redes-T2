import socket
import time
import zlib

HOST = '127.0.0.1'
PORT = 8080
WINDOW_SIZE = 4  # Tamanho inicial da janela de congestionamento (slow start)
TIMEOUT = 2  # Tempo de espera para timeout (segundos)

def calculate_crc(data):
    return zlib.crc32(data)

def divide_file(file_path):
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(10)
            if not chunk:
                break
            if len(chunk) < 10:
                chunk += b'\x00' * (10 - len(chunk))  # Adiciona o padding caso necessario
            yield chunk

def send_file(client_socket, file_path):
    sequence_number = 0
    congestion_window = WINDOW_SIZE
    ssthresh = 16  # Limite para mudança de slow start para congestion avoidance
    unacked_packets = []

    for chunk in divide_file(file_path):
        crc = calculate_crc(chunk)
        packet = f"{sequence_number}|{crc}".encode('utf-8') + chunk
        client_socket.sendto(packet, (HOST, PORT))
        unacked_packets.append(sequence_number)
        print(f"Enviado pacote {sequence_number} com CRC {crc}")

        sequence_number += 1

        # Espera por ACKs enquanto a janela de congestionamento estiver cheia
        if len(unacked_packets) >= congestion_window:
            start_time = time.time()
            while time.time() - start_time < TIMEOUT:
                try:
                    ack, _ = client_socket.recvfrom(1024)
                    ack = int(ack.decode('utf-8'))
                    if ack in unacked_packets:
                        unacked_packets.remove(ack)
                        if congestion_window < ssthresh:
                            congestion_window *= 2  # Slow Start
                        else:
                            congestion_window += 1  # Congestion Avoidance
                        print(f"Recebido ACK {ack}, janela de congestionamento ajustada para {congestion_window}")
                        break
                except socket.timeout:
                    congestion_window = WINDOW_SIZE
                    print("Timeout ocorrido, reiniciando janela de congestionamento para Slow Start")
                    break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    username = input("Digite seu nome de usuário: ")
    client_socket.sendto(f"/JOIN {username}".encode('utf-8'), (HOST, PORT))

    file_path = input("Digite o caminho do arquivo para enviar: ")
    send_file(client_socket, file_path)

    client_socket.sendto("/QUIT".encode('utf-8'), (HOST, PORT))

if __name__ == "__main__":
    main()
