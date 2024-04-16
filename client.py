import grpc
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'protos')))

from protos import auth_pb2
from protos import auth_pb2_grpc

def register_user(stub):
    print("Enter user details:")
    username = input("Username: ")
    password = input("Password: ")
    person_name = input("Person Name: ")
    person_age = input("Person Age: ")
    person_mail = input("Person Mail: ")
    
    response = stub.RegisterUser(auth_pb2.RegisterUserRequest(
        username=username,
        password=password,
        person_name=person_name,
        person_age=person_age,
        person_mail=person_mail
    ))
    if response.success:
        print("User registered successfully.")
    else:
        print("Failed to register user.")

def login(stub):
    print("Enter login details:")
    username = input("Username: ")
    password = input("Password: ")
    
    response = stub.Login(auth_pb2.LoginRequest(
        username=username,
        password=password
    ))
    if response.success:
        print("Login successful.")
        print("Token:", response.token)
    else:
        print("Login failed.")

def run():
    channel = grpc.insecure_channel('192.168.1.19:50051')
    stub = auth_pb2_grpc.YourServiceStub(channel)
    
    print("1. Register User")
    print("2. Login")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == '1':
        register_user(stub)
    elif choice == '2':
        login(stub)
    else:
        print("Invalid choice. Please enter 1 or 2.")

if __name__ == '__main__':
    run()
