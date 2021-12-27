# Importar bibliotecas
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
# instalar requests==2.18.4 o 2.25.1
import requests
# biblioteca de identificadores únicos
from uuid import uuid4
# Conectar, recibir direcciones
from urllib.parse import urlparse

# Parte 1 - Crear una cadena de bloques
class Blockchain:
    
    def __init__(self):
        self.chain = []
        # lista de transacciones(mempool)
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        # Crear una colección/conjunto no ordenada de nodos
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain)+1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
            }
        # Una vez creado el bloque, vaciar la lista de transacciones
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1 
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        print(encoded_block)
        return hashlib.sha256(encoded_block).hexdigest()
        
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender, 'receiver': receiver, 'amount': amount})
        previous_block = self.get_previous_block()+1
        return previous_block['index']+1

    def add_node(self, address):
        # solamente nos interesa el dominio y puerto
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain) # supuestamente mi cadena es la más larga
        # localizar quien tiene la cadena mas larga
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # la cadena mas larga es la reina
                # validar que si mi cadena es menor a la cadena recibida Y si la cadena recibida es válida
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            # reemplazar la cadena
            self.chain = longest_chain
            return True
        return False
        
# Parte 2 - Minado de un bloque de la cadena

# Crear una aplicación web
app = Flask(__name__)

# Dirección del nodo en el puerto 5000
node_address = str(uuid4()).replace('-','')

# En caso de error 500
# app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Crear una Blockchain
blockchain = Blockchain()

# Minar un nuevo bloque
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # Pagar al minero
    blockchain.add_transaction(sender = node_address, receiver = "Celina", amount = 10)
    # Se crea el bloque, incluido el pago al minero
    new_block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': '¡Has minado un nuevo bloque!',
        'index': new_block['index'],
        'timestamp': new_block['timestamp'],
        'proof': new_block['proof'],
        'previous_hash': new_block['previous_hash'],
        'transactions': new_block['transactions']
        }
    return jsonify(response), 200

# Obtener la cadena de bloques al completo
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
        }
    return jsonify(response), 200

@app.route('/is_valid', methods=['GET'])
def is_valid():
    response = {
        'datetime': str(datetime.datetime.now()),
        'health_status': blockchain.is_chain_valid(blockchain.chain) if 'Good' else 'Bad'
        }
    return jsonify(response), 200

# Añadir una nueva transacción a la cadena de bloques
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_key = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_key):
        return 'Faltan algunos elementos de la transacción', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'La transacción será añadida al bloque {index}'}
    return jsonify(response), 201

# Parte 3 - Descentralizar la cadena de bloques

# Conectar nuevos nodos
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    # conectar un nuevo nodo a todos los nodos
    nodes = json.get('nodes')
    if nodes is None:
        return 'No hay nodos para añadir', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': f'Todos los nodos han sido conectados. La cadena de JGcoins contiene ahora los nodos siguientes ',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Reemplazar la cadena por la más larga (si es necesario)
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'Los nodos tenían diferentes cadenas, que han sido todas reemplazadas por la más larga.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'La cadena no ha sido reemplazada. Todo esta bien :)',
                    'current_chain': blockchain.chain}
    return jsonify(response), 200

# Ejecutar la app
app.run('0.0.0.0', port = 5003)

