import socket
import tkinter as tk
from tkinter import scrolledtext
import sqlite3
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

# Create a server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 9999))
server.listen(1)  # Listen for incoming connections (1 connection at a time)

# Connect to the SQLite database or create a new one
conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()

# Create a table to store chat history
cursor.execute("CREATE TABLE IF NOT EXISTS chat_history (message_id INTEGER PRIMARY KEY, sender TEXT, message_encoded BLOB, message_decoded TEXT)")

print("Server is listening for incoming connections...")

# Accept a connection from a client
client, addr = server.accept()

# Generate RSA key pair for the server
server_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
server_public_key = server_private_key.public_key()

# Share the server's public key with the client
client.send(server_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
))

done = False

# List to store chat history
chat_log = []

# Function to update the chat log in the server GUI
def update_chat_log():
    server_chat_log.delete(1.0, tk.END)
    server_chat_log.insert(tk.END, "\n".join(chat_log))

# Create a Tkinter window for the server GUI
server_window = tk.Tk()
server_window.title("Chat Server")

# Create a scrolled text widget to display the chat log
server_chat_log = scrolledtext.ScrolledText(server_window)
server_chat_log.pack()

while not done:
    try:
        encrypted_msg = client.recv(2048)  # Adjust the buffer size as needed

        # Decrypt the received message using the server's private key
        decrypted_msg = server_private_key.decrypt(
            encrypted_msg,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        decrypted_msg = decrypted_msg.decode('utf-8')

        if decrypted_msg == 'quit':
            done = True
        else:
            print("Client:", decrypted_msg)

            # Insert the received message into the database
            cursor.execute("INSERT INTO chat_history (sender, message_encoded, message_decoded) VALUES (?, ?, ?)", ("Client", encrypted_msg, decrypted_msg))
            conn.commit()

            response = input("Server: ").encode('utf-8')

            # Encrypt the response before sending it back to the client
            response_encrypted = server_public_key.encrypt(
                response,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Store the server's response in the database
            cursor.execute("INSERT INTO chat_history (sender, message_encoded, message_decoded) VALUES (?, ?, ?)", ("Server", response_encrypted, response))
            conn.commit()

            chat_log.append("Server: " + response.decode('utf-8'))
            update_chat_log()
    except Exception as e:
        print("An error occurred:", e)

# Close the client, server sockets, and the database connection
client.close()
server.close()
conn.close()

# Start the server GUI event loop
server_window.mainloop()
