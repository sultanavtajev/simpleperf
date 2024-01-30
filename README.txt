SIMPLEPERF
Simpleperf is a lightweight network performance measurement tool. It can run in 
server or client mode. In server mode, it listens for incoming client connections and
receives data sent by clients. In client mode, it connects to a server and sends data
to the server. The performance statistics include the transfer rate between the
client and the server.

FEATURES
Server mode: Binds to a specified IP address, listens on a specific port, and calculates the transfer rate based on the data received from clients.
Client mode: Connects to a server using the server's IP address and port, sends data to the server for a specified duration, and displays the transfer rate at specified intervals.
Supports parallel connections to the server in client mode.
Customizable format for displaying the summary of results (B, KB, or MB).
Validation of IP addresses, port numbers, and other user-provided arguments.

REQUIREMENTS
Python 3.x

INSTALLATION 
Clone the repository or download the script simpleperf.py.
Make sure you have Python 3.x installed on your system.

USAGE
Navigate to the directory where the script is saved.
Run the script in server mode: python simpleperf.py -s
Run the script in client mode: python simpleperf.py -c -I <server_ip>
Replace <server_ip> with the IP address of the server you want to connect to.

ADDITIONAL COMMAND LINE ARGUMENTS
Server Mode:
-b, --bind: Bind to the specified IP address (default: 127.0.0.1).
-p, --port: Select the port number on which the server should listen (default: 8088).
-f, --format: Choose the format of the summary of results (B, KB, or MB, default: MB).

Client Mode:
-I, --serverip: Select the IP address of the server (required).
-t, --time: The total duration in seconds for which data should be generated and sent to the server (default: 25).
-i, --interval: Print statistics per z seconds (optional).
-P, --parallel: Number of parallel connections to create (default: 1).
-n, --num: Transfer the number of bytes specified by the -n flag (optional).