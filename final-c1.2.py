import socket
import tkinter as tk
from tkinter import scrolledtext
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

# Create a socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Define the server's address as a tuple (host, port)
server_address = ("localhost", 9999)

# Connect to the server
client.connect(server_address)

# Create a Tkinter window
window = tk.Tk()
window.title("Chat Client")

# Create a scrolled text widget to display the chat history
chat_history = scrolledtext.ScrolledText(window)
chat_history.pack()

# Create an entry widget to type messages
message_entry = tk.Entry(window)
message_entry.pack()

# List to store chat history
chat_log = []

# Generate RSA key pair for the client
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

# Receive the server's public key from the server
server_public_key_pem = client.recv(2048)  # Adjust the buffer size as needed
server_public_key = serialization.load_pem_public_key(server_public_key_pem)

def send_message():
    message = message_entry.get()

    # Encrypt the message with the server's public key
    message_encrypted = server_public_key.encrypt(
        message.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Send the encrypted message to the server
    client.send(message_encrypted)

    chat_log.append("Client: " + message)
    chat_history.insert(tk.END, "Client: " + message + "\n")

    message_entry.delete(0, tk.END)

# Create a "Send" button
send_button = tk.Button(window, text="Send", command=send_message)
send_button.pack()

def receive_message():
    while True:
        try:
            encrypted_msg = client.recv(2048)  # Adjust the buffer size as needed

            # Decrypt the received message using the client's private key
            decrypted_msg = private_key.decrypt(
                encrypted_msg,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            decrypted_msg = decrypted_msg.decode('utf-8')

            chat_log.append("Server: " + decrypted_msg)
            chat_history.insert(tk.END, "Server: " + decrypted_msg + "\n")
        except Exception as e:
            print("An error occurred:", e)

# Create a separate thread to receive messages from the server
import threading
receive_thread = threading.Thread(target=receive_message)
receive_thread.start()

# Start the client GUI event loop
window.mainloop()
