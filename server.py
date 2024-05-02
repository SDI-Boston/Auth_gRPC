import sys
import os
from concurrent import futures
import grpc
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import jwt
import hashlib
from datetime import datetime, timedelta
from flask import Flask, jsonify
from flask_cors import CORS

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'protos'))

import auth_pb2
import auth_pb2_grpc

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
    UserPassword = Column(String(64), nullable=False)
    Person_idperson = Column(Integer, ForeignKey('Person.idperson'), nullable=False)
    person = relationship("Person")

class Logs(Base):
    __tablename__ = 'Logs'
    idLogs = Column(Integer, primary_key=True)
    LoginTimestamp = Column(TIMESTAMP, nullable=False)
    User_idUser = Column(Integer, ForeignKey('User.idUser'), nullable=False)
    User_Person_idperson = Column(Integer, ForeignKey('User.Person_idperson'), nullable=False)
    IPAddress = Column(String(45), nullable=False)  # Nueva columna para la dirección IP del cliente
    ModifiedBy = Column(String(45))
    ModifiedTimestamp = Column(TIMESTAMP)

engine = create_engine('mariadb://db:passwd*/@localhost/UsergRPC')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

SECRET_KEY = '4C70ECF8E61536D1F4C3D66DF751C5AFB44580067D9E7ADB25E8122D0EE037FA'

def generate_token(username, user_id, person_id, person_name, person_age, person_mail):
    payload = {
        'username': user_id,
        'user_id': username,
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

# Función para registrar los datos de logs
def register_log(user_id, person_id, ip_address, modified_by=None):
    try:
        current_time = datetime.now()
        log_entry = Logs(
            LoginTimestamp=current_time,
            User_idUser=user_id,
            User_Person_idperson=person_id,
            IPAddress=ip_address,  # Se pasa la dirección IP del cliente
            ModifiedBy=modified_by,
            ModifiedTimestamp=current_time
        )
        session.add(log_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error al registrar el log: {e}")

class AuthenticationService(auth_pb2_grpc.AuthenticationServiceServicer):
    def AuthenticateUser(self, request, context):
        user = session.query(User).filter_by(UserName=request.username).first()
        if not user:
            return auth_pb2.AuthenticationResponse(success=False, error_message="User not found")
        
        hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
        if user.UserPassword != hashed_password:
            return auth_pb2.AuthenticationResponse(success=False, error_message="Incorrect password")
        
        token = generate_token(user.UserName, user.idUser, user.Person_idperson, user.person.PersonName, user.person.PersonAge, user.person.PersonMail)

        # Registrar el inicio de sesión en los logs
        ip_address = context.peer()  # Obtiene la dirección IP del cliente que realizó la solicitud gRPC
        register_log(user.idUser, user.Person_idperson, ip_address)

        return auth_pb2.AuthenticationResponse(success=True, token=token)
    
    def RegisterUser(self, request, context):
        try:
            if session.query(User).filter_by(UserName=request.username).first():
                return auth_pb2.RegisterResponse(success=False, error_message="Username already exists")

            person = Person(PersonName=request.name, PersonAge=request.age, PersonMail=request.email)
            session.add(person)
            session.flush()
            
            hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
            user = User(UserName=request.username, UserPassword=hashed_password, Person_idperson=person.idperson)
            session.add(user)
            session.commit()
            
            # Registrar el evento en los logs
            ip_address = context.peer()  # Obtiene la dirección IP del cliente que realizó la solicitud gRPC
            register_log(user.idUser, user.Person_idperson, ip_address)

            return auth_pb2.RegisterResponse(success=True, message="User registered successfully")
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.RegisterResponse(success=False, error_message="Internal server error")

class RegisterService(auth_pb2_grpc.RegisterServiceServicer):
    def RegisterUser(self, request, context):
        try:
            if session.query(User).filter_by(UserName=request.username).first():
                return auth_pb2.RegisterResponse(success=False, error_message="Username already exists")

            person = Person(PersonName=request.name, PersonAge=request.age, PersonMail=request.email)
            session.add(person)
            session.flush() 

            hashed_password = hashlib.sha256(request.password.encode()).hexdigest()
            user = User(UserName=request.username, UserPassword=hashed_password, Person_idperson=person.idperson)
            session.add(user)
            session.commit()

            return auth_pb2.RegisterResponse(success=True, mensagge="User registered successfully")
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.RegisterResponse(success=False, error_message="Internal server error")

app = Flask(__name__)
CORS(app)  # Habilita CORS para todos los endpoints de la aplicación

# Configura la conexión a la base de datos
db_engine = create_engine('mariadb://db:passwd*/@localhost/UsergRPC')
Session = sessionmaker(bind=db_engine)

# Ruta para obtener todos los usuarios
@app.route('/users', methods=['GET'])
def get_users():
    session = Session()
    users = session.query(User).all()
    session.close()
    user_list = [{'id': user.idUser, 'username': user.UserName} for user in users]
    return jsonify(user_list)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthenticationServiceServicer_to_server(AuthenticationService(), server)
    auth_pb2_grpc.add_RegisterServiceServicer_to_server(RegisterService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server running on port 50051")

    # No bloquea la ejecución del servidor gRPC
    app.run(debug=True, use_reloader=False, port=5001)

if __name__ == '__main__':
    serve()
