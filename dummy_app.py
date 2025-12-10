from flask import Flask, request, jsonify
import logging

# Configuration des logs : tout ce qui se passe sera écrit dans /var/log/dummy_app.log
logging.basicConfig(filename='/var/log/dummy_app.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

app = Flask(__name__)

# Simule une base de données d'utilisateurs en mémoire
users_db = {} 

# Endpoint pour voir qui est dans l'app (GET)
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users_db)

# Endpoint pour créer ou mettre à jour un utilisateur (POST)
@app.route('/api/users/<uid>', methods=['POST'])
def create_user(uid):
    data = request.json
    # On stocke l'utilisateur dans le dictionnaire
    users_db[uid] = data
    # On écrit dans le journal
    logging.info(f"[PROVISIONING] Ajout/Update de l'utilisateur {uid} (Role: {data.get('role')})")
    return jsonify({"status": "success", "msg": f"User {uid} created"}), 201

# Endpoint pour supprimer un utilisateur (DELETE)
@app.route('/api/users/<uid>', methods=['DELETE'])
def delete_user(uid):
    if uid in users_db:
        del users_db[uid]
        logging.info(f"[DE-PROVISIONING] Suppression de l'utilisateur {uid}")
        return jsonify({"status": "success", "msg": "User deleted"}), 200
    
    logging.warning(f"[ERROR] Tentative de suppression échouée : {uid} inconnu.")
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    # L'app écoute sur toutes les interfaces (0.0.0.0) port 5000
    app.run(host='0.0.0.0', port=5000)