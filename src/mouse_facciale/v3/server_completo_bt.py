import bluetooth
import pyautogui

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", 1))  # Usa la stessa porta del client
server_sock.listen(1)

print("In attesa di connessione Bluetooth...")
client_sock, address = server_sock.accept()
print(f"Connesso a: {address}")

try:
    while True:
        data = client_sock.recv(1024)
        if not data:
            break

        decoded = data.decode().strip()
        print("Ricevuto:", decoded)

        parts = decoded.split()

        if not parts:
            continue

        command = parts[0]

        try:
            if command == "MOVE":
                dx, dy = int(parts[1]), int(parts[2])
                pyautogui.moveRel(dx, dy)

            elif command == "GOTO":
                x, y = int(parts[1]), int(parts[2])
                pyautogui.moveTo(x, y)

            elif command == "CLICK":
                pyautogui.click()

            elif command == "RIGHT_CLICK":
                pyautogui.rightClick()

            elif command == "DOUBLE_CLICK":
                pyautogui.doubleClick()

            elif command == "DOWN":
                button = parts[1] if len(parts) > 1 else 'left'
                pyautogui.mouseDown(button=button)

            elif command == "UP":
                button = parts[1] if len(parts) > 1 else 'left'
                pyautogui.mouseUp(button=button)

            elif command == "SCROLL":
                dx, dy = int(parts[1]), int(parts[2])
                pyautogui.hscroll(dx)
                pyautogui.scroll(dy)

            else:
                print(f"Comando sconosciuto: {command}")

        except Exception as e:
            print(f"Errore nell'esecuzione comando '{command}': {e}")

except KeyboardInterrupt:
    print("Interrotto da utente")

finally:
    client_sock.close()
    server_sock.close()
