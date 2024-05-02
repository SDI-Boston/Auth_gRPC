import sys
import os
import grpc

current_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(current_dir, 'protos'))

import auth_pb2
import auth_pb2_grpc

def login(stub):
    username = input("Enter username: ")
    password = input("Enter password: ")
    request = auth_pb2.UserCredentials(username=username, password=password)
    
    response = stub.AuthenticateUser(request)
    
    if response.success:
        print("Authentication successful.")
        print("Token:", response.token)
    else:
        print("Authentication failed.")
        print("Error:", response.error_message)

def register(stub):
    username = input("Enter username: ")
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    age = input("Enter your age: ")
    password = input("Enter password: ")

    request = auth_pb2.UserCredentialsRegister(
        username=username,
        name=name,
        email=email,
        age=age,
        password=password
    )

    response = stub.RegisterUser(request)

    if response.success:
        print("Registration successful.")
        print("Message:", response.mensagge)
    else:
        print("Registration failed.")
        print("Error:", response.error_message) 

def run():
    with grpc.insecure_channel('172.171.240.20:50051') as channel:
        auth_stub = auth_pb2_grpc.AuthenticationServiceStub(channel)
        
        register_stub = auth_pb2_grpc.RegisterServiceStub(channel)

        choice = input("Choose an option:\n1. Login\n2. Register\n")
        
        if choice == '1':
            login(auth_stub)
        elif choice == '2':
            register(register_stub) 
        else:
            print("Invalid choice. Please choose either 1 or 2.")


if __name__ == '__main__':
    run()
