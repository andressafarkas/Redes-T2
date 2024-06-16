import socket
import zlib

HOST = '127.0.0.1'
PORT = 8080

def calculate_crc(data):
    return zlib.crc32(data)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, PORT))

    print("Servidor UDP iniciado...")

    received_data = {}
    expected_sequence = 0

    while True:
        try:
            data, client_address = server_socket.recvfrom(1024)
            sequence_number, crc, chunk = data.decode('utf-8').split('|', 2)
            sequence_number = int(sequence_number)
            crc = int(crc)
            chunk = chunk.encode('utf-8')

            if calculate_crc(chunk) == crc:
                if sequence_number == expected_sequence:
                    received_data[sequence_number] = chunk
                    expected_sequence += 1
                    ack = f"{sequence_number + 1}".encode('utf-8')
                    server_socket.sendto(ack, client_address)
                    print(f"Recebido pacote {sequence_number} com CRC {crc}, enviado ACK {sequence_number + 1}")
                else:
                    ack = f"{expected_sequence}".encode('utf-8')
                    server_socket.sendto(ack, client_address)
                    print(f"Pacote fora de ordem. Esperado: {expected_sequence}, Recebido: {sequence_number}")
            else:
                print(f"Erro de CRC no pacote {sequence_number}")

        except Exception as e:
            print(f"Erro ao receber pacote: {e}")
            break

    with open('arquivo_reconstruido.txt', 'wb') as f:
        for seq in sorted(received_data.keys()):
            if seq == max(received_data.keys()):  # Last packet
                chunk = received_data[seq].rstrip(b'\x00')  # Remove padding
            else:
                chunk = received_data[seq]
            f.write(chunk)
        print("Arquivo reconstruído salvo como 'arquivo_reconstruido.txt'")

if __name__ == "__main__":
    main()
