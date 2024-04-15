import sys
import os
from concurrent import futures
import grpc
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import jwt
from datetime import datetime, timedelta
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'protos')))

Base = declarative_base()

class Person(Base):
    __tablename__ = 'Person'
    idperson = Column(Integer, primary_key=True)
    PersonName = Column(String(45), nullable=False)
    PersonAge = Column(String(45), nullable=False)
    PersonMail = Column(String(45), nullable=False)

class User(Base):
    __tablename__ = 'User'
    idUser = Column(Integer, primary_key=True)
    UserName = Column(String(45), nullable=False, unique=True)
    UserPassword = Column(String(64), nullable=False)  # Changed length to accommodate SHA256 hash
    Person_idperson = Column(Integer, ForeignKey('Person.idperson'), nullable=False)
    person = relationship("Person")

engine = create_engine('mysql://root:1629@localhost/usergrpc')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

SECRET_KEY = 'gRPC_*'

def generate_token(username, user_id, person_id, person_name, person_age, person_mail):
    payload = {
        'username': username,
        'user_id': user_id,
        'person_id': person_id,
        'person_name': person_name,
        'person_age': person_age,
        'person_mail': person_mail,
        'exp': datetime.utcnow() + timedelta(days=7) 
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}

import auth_pb2
import auth_pb2_grpc

class YourServiceServicer(auth_pb2_grpc.YourServiceServicer):
    def RegisterUser(self, request, context):
        # Convertir la contraseña a SHA256
        hashed_password = hashlib.sha256(request.password.encode()).hexdigest()

        new_person = Person(PersonName=request.person_name, PersonAge=request.person_age, PersonMail=request.person_mail)
        session.add(new_person)
        session.commit()
        new_user = User(UserName=request.username, UserPassword=hashed_password, person=new_person)
        session.add(new_user)
        session.commit()
        token = generate_token(request.username, new_user.idUser, new_person.idperson, request.person_name, request.person_age, request.person_mail)
        return auth_pb2.RegisterUserResponse(success=True, token=token)

    def RegisterPerson(self, request, context):
        new_person = Person(PersonName=request.person_name, PersonAge=request.person_age, PersonMail=request.person_mail)
        session.add(new_person)
        session.commit()
        return auth_pb2.RegisterPersonResponse(success=True)

    def Login(self, request, context):
        # Convertir la contraseña a SHA256
        hashed_password = hashlib.sha256(request.password.encode()).hexdigest()

        user = session.query(User).filter_by(UserName=request.username, UserPassword=hashed_password).first()
        if user:
            token = generate_token(request.username, user.idUser, user.person.idperson, user.person.PersonName, user.person.PersonAge, user.person.PersonMail)
            return auth_pb2.LoginResponse(success=True, token=token)
        else:
            return auth_pb2.LoginResponse(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_YourServiceServicer_to_server(YourServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server running on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
