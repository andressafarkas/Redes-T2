import socket
import threading
import time
import zlib

HOST = '127.0.0.1'
PORT = 8080
WINDOW_SIZE = 4  # Tamanho inicial da janela de congestionamento (slow start)
TIMEOUT = 2  # Tempo de espera para timeout (segundos)

def calculate_crc(data): 
    return zlib.crc32(data)

def divide_file(file_path): # Divide o arquivo em partes de 10 bytes
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(10)
            if not chunk:
                break
            yield chunk

def receive_ack(client_socket): # Recebe e exibe os ACKs
    while True:
        try:
            ack, _ = client_socket.recvfrom(1024)
            ack = ack.decode('utf-8')
            print(f"Recebido ACK: {ack}")
        except Exception as e:
            print(f"Erro ao receber ACK: {e}")
            break

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

        # Slow Start e Congestion Avoidance
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
                        break
                except socket.timeout:
                    congestion_window = WINDOW_SIZE
                    break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)

    username = input("Digite seu nome de usuário: ")
    client_socket.sendto(f"/JOIN {username}".encode('utf-8'), (HOST, PORT))

    receive_thread = threading.Thread(target=receive_ack, args=(client_socket,))
    receive_thread.start()

    file_path = input("Digite o caminho do arquivo para enviar: ")
    send_file(client_socket, file_path)

    client_socket.sendto("/QUIT".encode('utf-8'), (HOST, PORT))

if __name__ == "__main__":
    main()
