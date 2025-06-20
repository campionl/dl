import bluetooth
import pyautogui
import sys

# Impostazioni del server Bluetooth
SERVER_PORT = 1       # Porta standard per i servizi Bluetooth (puoi cambiarla, ma assicurati che sia la stessa sul client)
SERVER_NAME = "MouseControlServer" # Nome del servizio (utile per la scoperta da parte del client)

def run_server():
    # Ottieni le dimensioni dello schermo del server
    screen_width, screen_height = pyautogui.size()
    print(f"Dimensioni dello schermo del server: {screen_width}x{screen_height}")

    # Crea un socket Bluetooth
    # bluetooth.RFCOMM è il protocollo più comune per la comunicazione seriale su Bluetooth
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", SERVER_PORT)) # Collega il socket a tutte le interfacce disponibili sulla porta specificata
    server_sock.listen(1) # Metti il socket in ascolto per una singola connessione in coda

    print(f"In attesa di connessioni sulla porta {SERVER_PORT}...")

    # Pubblica il servizio (facoltativo ma utile per la scoperta)
    # Advertise il servizio in modo che il client possa trovarlo per nome
    bluetooth.advertise_service(server_sock, SERVER_NAME,
                                service_classes=[bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE])

    client_sock, address = server_sock.accept() # Accetta una connessione in arrivo
    print(f"Accettata connessione da {address}")

    try:
        while True:
            # Ricevi i dati dal client
            # La dimensione del buffer (1024) è tipicamente sufficiente per piccole quantità di dati come le coordinate
            data = client_sock.recv(1024).decode('utf-8')
            if not data:
                break # Se non ci sono dati, la connessione è stata chiusa dal client
            
            # Parsifica i dati ricevuti (formato "x,y")
            try:
                client_x, client_y = map(int, data.split(','))
            except ValueError:
                print(f"Dati non validi ricevuti: {data}")
                continue

            # Mappa le coordinate del client alle dimensioni dello schermo del server
            # Assumiamo che il client invii coordinate assolute basate sulla sua risoluzione
            # Per una mappatura relativa, avremmo bisogno anche della risoluzione dello schermo del client
            # Per ora, supponiamo che il client invii valori da 0 a MAX_CLIENT_X e 0 a MAX_CLIENT_Y.
            # Se i client hanno risoluzioni diverse, questo è un punto critico.
            # Per una mappatura veramente relativa senza conoscere la risoluzione del client,
            # il client dovrebbe inviare le coordinate come percentuali (0.0-1.0).

            # Per semplicità, qui mappiamo direttamente le coordinate assolute
            # Supponiamo che il client invii coordinate relative al suo schermo,
            # e per spostare il mouse del server nella stessa posizione *relativa*,
            # dobbiamo sapere le dimensioni dello schermo del client.
            # Senza di esse, possiamo solo assumere che il client invii coordinate assolute e scalarle.
            
            # Per una soluzione più robusta: il client dovrebbe inviare le sue dimensioni dello schermo una volta all'inizio.
            # In questo esempio, *assumeremo* che le coordinate in arrivo siano già proporzionali allo schermo del server,
            # o che le risoluzioni siano uguali. Se non lo sono, il movimento potrebbe essere "sfasato".
            
            # Per un movimento fluido, pyautogui.moveTo() è ottimo.
            # La durata (duration) può essere impostata per un movimento più graduale.
            
            # Qui usiamo la logica di scalatura se le risoluzioni sono diverse.
            # Tuttavia, senza la risoluzione del client, questa è una stima.
            # Idealmente, il client invierebbe `(current_x / client_width, current_y / client_height)`
            # e il server calcolerebbe `target_x = percent_x * server_width`, `target_y = percent_y * server_height`.

            # DEBUG: Se vuoi stampare le coordinate ricevute
            # print(f"Ricevuto: {client_x},{client_y}")

            # Sposta il mouse del server
            # pyautogui.moveTo(client_x, client_y, duration=0.01) # duration per un movimento più fluido
            
            # Per un movimento più preciso e relativo, avremmo bisogno delle dimensioni dello schermo del client.
            # In mancanza di ciò, facciamo un'assunzione semplificata:
            # mappiamo le coordinate del client come se il client avesse la stessa risoluzione del server.
            # Se le risoluzioni sono diverse, il movimento non sarà perfettamente "relativo".
            
            # Per una mappatura veramente relativa:
            # Il client dovrebbe inviare (client_x, client_y, client_screen_width, client_screen_height)
            # E il server calcolerebbe:
            # percent_x = client_x / client_screen_width
            # percent_y = client_y / client_screen_height
            # target_x = int(percent_x * screen_width)
            # target_y = int(percent_y * screen_height)
            
            # Dato che non abbiamo le dimensioni dello schermo del client qui,
            # sposteremo il mouse direttamente alle coordinate ricevute.
            # Questo significa che il movimento sarà "relativo" solo se le risoluzioni sono identiche.
            # Altrimenti, si avrà un effetto di scaling implicito.
            
            # Per un movimento più fluido, usa un valore basso per duration.
            # Valori troppo bassi possono rendere il movimento scattoso se i dati arrivano lentamente.
            # Valori più alti lo rendono più "trascinato". 0.05 è un buon compromesso.
            pyautogui.moveTo(client_x, client_y, duration=0.05) 

    except bluetooth.BluetoothError as e:
        print(f"Errore Bluetooth: {e}")
    except KeyboardInterrupt:
        print("Server terminato dall'utente.")
    finally:
        print("Chiusura del socket client e server.")
        if client_sock:
            client_sock.close()
        server_sock.close()
        sys.exit()

if __name__ == "__main__":
    run_server()