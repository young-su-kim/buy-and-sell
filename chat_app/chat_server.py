import socket
import threading
from typing import Dict

# 간단한 채팅 서버 (TCP) - 한국어 전용
# 1원 당 1C 포인트 전환

HOST = '0.0.0.0'
PORT = 9009

clients = {}
balances: Dict[str, int] = {}
lock = threading.Lock()

def broadcast(message: str, exclude=None):
    for username, conn in clients.items():
        if username == exclude:
            continue
        try:
            conn.sendall(message.encode('utf-8'))
        except Exception:
            pass

def handle_client(conn: socket.socket, addr):
    conn.sendall('USERNAME?\n'.encode('utf-8'))
    username = conn.recv(1024).decode('utf-8').strip()
    with lock:
        clients[username] = conn
        balances.setdefault(username, 0)
    broadcast(f"[시스템] {username}님이 입장했습니다.\n", exclude=username)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode('utf-8').strip()
            if msg.startswith('MSG '):
                text = msg[4:]
                broadcast(f"[{username}] {text}\n", exclude=None)
            elif msg.startswith('CARD ') or msg.startswith('CASH '):
                try:
                    amount = int(msg.split()[1])
                except (IndexError, ValueError):
                    conn.sendall('금액을 입력하세요.\n'.encode('utf-8'))
                    continue
                with lock:
                    balances[username] += amount
                conn.sendall(f"포인트 충전 완료: {amount}C (잔액 {balances[username]}C)\n".encode('utf-8'))
            elif msg == 'BALANCE':
                with lock:
                    bal = balances.get(username, 0)
                conn.sendall(f"잔액: {bal}C\n".encode('utf-8'))
            elif msg == 'QUIT':
                break
            else:
                conn.sendall('명령을 인식할 수 없습니다.\n'.encode('utf-8'))
    finally:
        with lock:
            clients.pop(username, None)
        broadcast(f"[시스템] {username}님이 퇴장했습니다.\n", exclude=username)
        conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"서버 시작: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main()
