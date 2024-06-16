import socket
import zlib

def calculate_crc(data):
    return zlib.crc32(data) & 0xffffffff

def start_server(host='localhost', port=12345):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print("Server started at {}:{}".format(host, port))

    expected_seq_num = 0
    file_data = b""

    while True:
        data, address = sock.recvfrom(1024)
        if not data:
            break

        seq_num = int.from_bytes(data[:4], 'big')
        received_crc = int.from_bytes(data[4:8], 'big')
        payload = data[8:]

        if calculate_crc(payload) == received_crc:
            if seq_num == expected_seq_num:
                file_data += payload
                expected_seq_num += 1
            ack = (seq_num + 1).to_bytes(4, 'big')
            sock.sendto(ack, address)
        else:
            print("Error detected in packet {}".format(seq_num))
            ack = expected_seq_num.to_bytes(4, 'big')
            sock.sendto(ack, address)

    with open('received_file.txt', 'wb') as f:
        f.write(file_data)

    print("File received and saved as received_file.txt")

if __name__ == "__main__":
    start_server()
