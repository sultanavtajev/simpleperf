
# Description:
# Imports the necessary libraries
# socket: Low-level networking interface for Python, allowing us to create and work with sockets.
# argparse: Used for parsing command-line arguments.
# time: Provides various time-related functions. 
# sys: Provides access to some variables and functions maintained by the interpreter.
# ipaddress: Provides classes for manipulating and working with IPv4 and IPv6 addresses and networks.
# threading: Used for creating and managing threads in a Python program.
# functools: Provides higher-order functions and operations on callable objects like functions, methods, or classes. 
import socket
import argparse
import time
import sys
import ipaddress
import threading
from functools import partial

# Description:
# Function: Defines a helper function that prints an error message and exits the program
# Arguments:
# error_message: A string representing the error message to be displayed.
# Returns: None.
def print_error(error_message):
    print("Error: " + error_message)
    sys.exit(1)


# Description:
# A custom thread class that allows a return value to be fetched after the thread has completed its execution.
# Attributes:
# _return_value: Stores the return value of the target function.
# Methods:
# run(): Overrides the run method of the base class to store the return value of the target function.
# result(): Returns the _return_value attribute.
class ReturnValueThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._return_value = None
        
    # Function: Executes the target function with its arguments and stores the result.
    def run(self):
        if self._target is not None:
            self._return_value = self._target(*self._args, **self._kwargs)
            
    # Function: Returns the result of the target function.
    # Returns: The result of the target function.
    def result(self):
        return self._return_value

# Description:
# Creates a server that listens for incoming connections and handles clients using threads.
# Arguments:
# bind_address: A string containing the IP address to bind the server socket to.
# port: An integer representing the port number to listen for incoming connections.
# buffer_size: An integer representing the size of the buffer used for receiving data.
# format: A string indicating the format of the summary of results ('B', 'KB', or 'MB').
# Returns: None.
def server_mode(bind_address, port, buffer_size, format):
    # Create a socket object for IPv4 and TCP connection
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reuse of address and port
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the server socket to the given IP address and port number
    server_socket.bind((bind_address, port))
    # Listen for incoming connections with a backlog of 5
    server_socket.listen(5)
    
    # Print server information
    print(f"-------------------------------------------------\n"
          f"| A simpleperf server is listening on port {port} |\n"
          f"-------------------------------------------------")

    # Description:
    # Handles data transfer with a connected client and calculates performance statistics.
    # Arguments:
    # client_socket: A socket object representing the connection with the client.
    # client_address: A tuple containing the client's IP address and port number.
    # Returns: None.
    def handle_client(client_socket, client_address):
        # Print a message indicating that a client is connected
        print(f"---------------------------------------------------------------------------------------------\n"
              f"| A simpleperf client with {client_address} is connected with {server_socket.getsockname()} |\n"
              f"---------------------------------------------------------------------------------------------")

        # Initialize variables for tracking data transfer and elapsed time
        start_time = time.time()
        data_received = 0

        # Receive data from the client until "bye" is received
        while True:
            data = client_socket.recv(buffer_size)
            if b"bye" in data:
                break
            data_received += len(data)
            
        # Calculate the elapsed time and format it as a string
        elapsed_time = time.time() - start_time
        elapsed_time_str = f"0.0 - {elapsed_time:.1f}"
        
        # Send an acknowledgement to the client and close the connection
        client_socket.send(b"ack")
        client_socket.close()

        # Format the data transfer size and rate as strings
        transfer, data_size = format_data(data_received, format)
        transfer_data_size = f"{transfer:.1f} {data_size}"
        if elapsed_time > 0:
            rate = (data_received * 8) / (1000000 * elapsed_time)
            rate_str = "{:.1f} Mbps".format(rate)
        else:
            rate_str = "N/A"

       # Print performance statistics for each connection
        server_id = f"{client_address[0]}:{client_address[1]}"
        print_statistics(server_id, elapsed_time_str,
                         transfer_data_size, rate_str, is_server=True)

    # Accept incoming connections and handle clients using threads
    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_address))
        client_thread.start()


# Description:
#  Connects to the server, sends data for a specified duration, and calculates performance statistics.
# Arguments:
# server_ip: A string containing the server's IP address.
# server_port: An integer representing the server's port number.
# buffer_size: An integer representing the size of the buffer used for sending data.
# duration: An integer representing the total duration (in seconds) for sending data to the server.
# format: A string indicating the format of the summary of results ('B', 'KB', or 'MB').
# interval: An integer representing the time interval (in seconds) for periodic reporting of performance statistics.
# parallel: An integer representing the number of parallel connections to create.
# num_bytes: An integer representing the number of bytes to send(specified by the '-n' flag).
# Returns: None.
def client_mode(server_ip, server_port, buffer_size, duration, format, interval, parallel, num_bytes):
    # Create a list of client sockets with length 'parallel'
    client_sockets = [socket.socket(
        socket.AF_INET, socket.SOCK_STREAM) for _ in range(parallel)]

    # Connect each client socket to the server
    for client_socket in client_sockets:
        client_socket.connect((server_ip, server_port))
        # Get the client ID from the socket's IP address and port number
        client_id = f"{client_socket.getsockname()[0]}:{client_socket.getsockname()[1]}"
        # Print a message indicating which client is connecting to the server
        print(f"-----------------------------------------------------------------------------------------\n"
              f"| A simpleperf client ({client_id}) connecting to server {server_ip}, port {server_port} |\n"
              f"-----------------------------------------------------------------------------------------")

    # If the user specified a number of bytes to transfer, convert it to bytes
    if num_bytes:
        num_bytes = int(num_bytes[:-2]) * (1000 **
                                           ['B', 'KB', 'MB'].index(num_bytes[-2:]))

    # Create a list of references to the amount of data sent from each client
    data_sent_ref = [0]

    # If the user specified an interval for periodic reporting, start a new thread to report statistics
    if interval:
        report_thread = threading.Thread(target=periodic_report, args=(
            f"{client_sockets[0].getsockname()[0]}:{client_sockets[0].getsockname()[1]}", time.time(), data_sent_ref, format, interval, duration))
        report_thread.daemon = True
        report_thread.start()

    # Create a partial function to send data to the server with the specified buffer size and duration
    send_data_partial = partial(send_data, buffer_size=buffer_size,
                                duration=duration, num_bytes=num_bytes, data_sent_ref=data_sent_ref)
    # Create a list of threads, one for each client socket, to send data to the server
    threads = [ReturnValueThread(target=send_data_partial, args=(
        client_socket,)) for client_socket in client_sockets]

    # Start each thread
    for thread in threads:
        thread.start()

    # Wait for each thread to finish and get the amount of data sent and the elapsed time for each thread
    for thread, client_socket in zip(threads, client_sockets):
        thread.join()
        data_sent, elapsed_time = thread.result()
        # Get the client ID from the socket's IP address and port number
        client_id = f"{client_socket.getsockname()[0]}:{client_socket.getsockname()[1]}"
        # Create a string representing the elapsed time
        elapsed_time_str = f"0.0 - {elapsed_time:.1f}"
        # Convert the amount of data sent to the specified format and create a string representing it
        transfer, data_size = format_data(data_sent, format)
        transfer_data_size = f"{transfer:.1f} {data_size}"
        # If the elapsed time is greater than 0, calculate the transfer rate and create a string representing it
        if elapsed_time > 0:
            rate = (data_sent * 8) / (1000000 * elapsed_time)
            rate_str = "{:.1f} Mbps".format(rate)
        else:
            rate_str = "N/A"

        # Print performance statistics for each connection
        print_statistics(client_id, elapsed_time_str,
                         transfer_data_size, rate_str, is_server=False)

        # Send a "bye" message to the server, wait for an acknowledgement, and close the client socket
        client_socket.send(b"bye")
        client_socket.recv(3)
        client_socket.close()


# Description:
#  Sends data over a socket connection.
# Arguments:
# client_socket: A socket object representing the client's connection to the server.
# buffer_size: The size of the buffer used to send data.
# duration: The duration (in seconds) for which to send data.
# num_bytes: The number of bytes to send. If set to None, the function will send data for the specified duration.
# data_sent_ref: A reference to a list that stores the amount of data sent. If not provided, this value will not be tracked.
# Returns: A tuple containing the amount of data sent and the elapsed time.
# Raises:
# socket.error: Raised if there is an error sending data over the socket.
# ValueError: Raised if any of the input arguments are invalid.
def send_data(client_socket, buffer_size, duration, num_bytes, data_sent_ref=None):
    # Initialize variables
    start_time = time.time()
    data_sent = 0
    data = b"0" * buffer_size
    
    # Send data for a specified number of bytes
    if num_bytes:
        bytes_to_send = num_bytes
        # Keep sending data until the specified number of bytes has been sent
        while bytes_to_send > 0:
            bytes_sent = client_socket.send(data[:bytes_to_send])
            bytes_to_send -= bytes_sent
            data_sent += bytes_sent
            # If data_sent_ref is not None, update its value to reflect the amount of data sent
            if data_sent_ref is not None:
                data_sent_ref[0] = data_sent
                
    # Send data for a specified duration
    else:
        # Keep sending data until the specified duration has elapsed
        while time.time() - start_time < duration:
            client_socket.send(data)
            data_sent += len(data)
            # If data_sent_ref is not None, update its value to reflect the amount of data sent
            if data_sent_ref is not None:
                data_sent_ref[0] = data_sent

    # Sleep for a short period of time before calculating elapsed time
    time.sleep(0.01)
    # Calculate the elapsed time since start_time
    elapsed_time = time.time() - start_time
    
    # Return the amount of data sent and the elapsed time
    return data_sent, elapsed_time

# Description:
# Generates periodic reports on the data transfer rate and amount of data sent for a client.
# Arguments:
# client_id: The ID of the client for which to generate the report.
# start_time: The start time ( in seconds since the epoch) of the data transfer.
# data_sent_ref: A reference to a list that stores the amount of data sent.
# format: The format in which to display the data transfer amount(e.g., "B", "KB", "MB", "GB").
# interval: The interval ( in seconds) at which to generate the report.
# duration: The duration ( in seconds) for which to generate the report.
# Returns: None.
# Raises:
# ValueError: Raised if any of the input arguments are invalid.
def periodic_report(client_id, start_time, data_sent_ref, format, interval, duration):
    
    # Initialize variables
    current_interval = 0
    prev_data_sent = 0
    
    # Generate reports at specified interval until duration is reached
    while current_interval < duration:
        # Pause for the specified interval
        time.sleep(interval)
        # Calculate elapsed time and amount of data sent
        elapsed_time = time.time() - start_time
        data_sent = data_sent_ref[0]
        # Calculate the amount of data sent during the current interval
        data_sent_interval = data_sent - prev_data_sent
        prev_data_sent = data_sent
        # Format the transfer size and rate as strings
        transfer, data_size = format_data(data_sent_interval, format)
        transfer_data_size = f"{transfer:.1f} {data_size}"
        rate = (data_sent_interval * 8) / (1000000 * interval)
        rate_str = "{:.2f} Mbps".format(rate)

        # Format the current interval as a string and print performance statistics
        interval_str = f"{current_interval:.1f} - {elapsed_time:.1f}"
        print_statistics(client_id, interval_str,
                         transfer_data_size, rate_str, is_server=False)

        # Update the current interval
        current_interval += interval


# Description:
# Formats the total data sent according to a specified format.
# Arguments:
# total_data_sent: The total amount of data sent.
# format: The format in which to display the data transfer amount(e.g., "B", "KB", "MB", "GB").
# Returns: A tuple containing the formatted data transfer amount and the size of the data.
# Raises:
# KeyError: Raised if an invalid format is provided.
# ValueError: Raised if the total data sent is negative.
def format_data(total_data_sent, format):
    # Initialize variables
    factor = {"B": 1, "KB": 1000, "MB": 1000000}[format]
    # Calculate formatted data transfer amount and size of data
    transfer = total_data_sent / factor
    data_size = "B" if factor == 1 else "KB" if factor == 1000 else "MB"
    # Return the formatted data transfer amount and size of data
    return transfer, data_size

# Description:
# Prints the statistics of data transfer between the client and the server.
# Arguments:
# server_id: The ID of the server or client.
# interval: The time interval during which data was transferred.
# transfer: The amount of data transferred during the specified interval.
# bandwidth: The bandwidth of data transfer during the specified interval.
# is_server: A boolean indicating whether the entity is a server or client. Defaults to True.
# Returns: None.
def print_statistics(server_id, interval, transfer, bandwidth, is_server=True):
    # Initialize variables
    transfer_label = "Received" if is_server else "Transfer"
    interval = interval + " s"
    # Print header if not printed before
    if not hasattr(print_statistics, "header_printed"):
        print_statistics.header_printed = {True: False, False: False}

    if not print_statistics.header_printed[is_server]:
        print(f"{'-' * 93}\n"
              f"| {'ID':<20} | {'Interval':<20} | {transfer_label:<20} | {'Bandwidth':<20} |\n"
              f"{'-' * 93}")
        # Mark header as printed for future calls to this function
        print_statistics.header_printed[is_server] = True
    # Print statistics
    print(f"| {server_id:<20} | {interval:<20} | {transfer:<20} | {bandwidth:<20} |")
    print(f"{'-' * 93}")


# Description:
# Validates the IP address format.
# Arguments:
# ip_address: A string containing an IPv4 address.
# Returns: True if the IP address is valid, False otherwise.
def validate_ip_address(ip_address):
    try:
        ipaddress.IPv4Address(ip_address)
        return True
    except ipaddress.AddressValueError:
        return False


# Description:
# Validates the port number to check if it's within the valid range (1024-65535).
# Arguments:
# port: An integer representing a port number.
# Returns: True if the port is valid, False otherwise.
def validate_port(port):
    try:
        port = int(port)
        if port <= 1024 or port >= 65535:
            return False
        return True
    except ValueError:
        return False

# Description:
# Validates the arguments passed in by the user.
# Arguments:
# args: The arguments to validate.
# Returns: The validated arguments.
# Raises: ValueError: Raised if the arguments are invalid.
def validate_args(args):
    # Check that either the -s or -c flag is used
    if not args.server and not args.client:
        print_error("You must run either in server or client mode")
    # Check that either the -s or -c flag is used, but not both
    if args.server and args.client:
        print_error("You must run either in server or client mode, not both")
    # Check that the -n flag is not used in server mode
    if args.server and args.num:
        print_error("SERVER: The -n flag is not supported in server mode")
    # Check that the server IP address is specified in client mode
    if args.client and not args.serverip:
        print_error(
            "CLIENT: You must specify the server IP address in client mode")
    # Check that the -n flag exists on the command line
    if args.num:
        # Convert the last two characters of the -n flag to lowercase
        suffix = args.num[-2:].lower()
        # Check that the -n flag contains b, kb or mb
        if suffix not in ['b', 'kb', 'mb']:
            print_error("CLIENT: Invalid b, kb or mb format for n-flag")
        try:
            # Extract all the numbers except the last two characters from the -n flag and convert it to an integer
            num_bytes = int(args.num[:-2])
        except ValueError:
            print_error("CLIENT: Invalid int conversion for -n flag")
        if num_bytes <= 0:
            print_error("CLIENT: The num_bytes must be greater than 0")
        if suffix == 'kb':
            num_bytes *= 1000
        elif suffix == 'mb':
            num_bytes *= 1000000
        args.num_bytes = num_bytes
    else:
        args.num_bytes = -1
    # Validate server IP address
    if args.server and args.bind:
        if not validate_ip_address(args.bind):
            print_error("SERVER: Invalid Server IP-address")
    # Validate client IP address
    if args.client and args.serverip:
        if not validate_ip_address(args.serverip):
            print_error("CLIENT: Invalid IP address")
    # Validate server port number
    if args.server and args.port:
        if not validate_port(args.port):
            print_error("SERVER: Invalid port number")
    # Validate client port number
    if args.client and args.port:
        if not validate_port(args.port):
            print_error("CLIENT: Invalid port number")
    # Validate time and num_bytes
    if args.client and args.time <= 0:
        print_error("CLIENT: Time must be greater than 0")
    return args

# Description:
# Initializes the program and parses the command line arguments.
# Arguments: None.
# Returns: None.
# Raises: 
# ValueError: Raised if the arguments are invalid.
def main():
    # Initialize the parser and add flags
    parser = argparse.ArgumentParser(description='simpleperf')
    # Server flags
    parser.add_argument('-s', '--server', action='store_true',
                        help='Enable the server mode')
    parser.add_argument("-b", "--bind", type=str, default="127.0.0.1",
                        help="Bind to the specified IP address (server mode)")
    parser.add_argument('-p', '--port', type=int, default=8088,
                        help='Select the port number on which the server should listen to')
    parser.add_argument('-f', '--format', choices=['B', 'KB', 'MB'],
                        default='MB', help='Choose the format of the summary of results')

    # Client flags
    parser.add_argument('-c', '--client', action='store_true',
                        help='Enable the client mode')
    parser.add_argument('-I', '--serverip', default='127.0.0.1',
                        help='Select the IP address of the server')
    parser.add_argument('-t', '--time', type=int, default=25,
                        help='The total duration in seconds for which data should be generated and sent to the server')
    parser.add_argument('-i', '--interval', type=int,
                        help='Print statistics per z second')
    parser.add_argument('-P', '--parallel', type=int, choices=range(1, 6),
                        default=1, help='Number of parallel connections to create')
    parser.add_argument('-n', '--num', type=str,
                        help='Transfer number of bytes specified by -n flag')
    args = parser.parse_args()

    # Validate the arguments
    args = validate_args(args)

    buffer_size = 1024

    # Check if server or client mode is enabled
    if args.server:
        # Start the program in server mode
        server_mode(args.bind, args.port, buffer_size, args.format)
    elif args.client:
        # Start the program in client mode
        client_mode(args.serverip, args.port, buffer_size, args.time,
                    args.format, args.interval, args.parallel, args.num)


# START
if __name__ == '__main__':
    main()
