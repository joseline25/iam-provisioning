import ldap3
import requests
import sys

# --- A. CONFIGURATION ---
# Adresses des deux autres VMs (définies dans /etc/hosts par Vagrant)
LDAP_HOST = 'iam-ldap'
API_HOST  = 'iam-app'

# Identifiants pour lire l'annuaire
LDAP_USER = 'cn=admin,dc=iam,dc=lab'
LDAP_PWD  = 'admin'

# URL de l'API de l'application cible
APP_URL   = f'http://{API_HOST}:5000/api/users'


# --- B. FONCTIONS UTILITAIRES ---

def get_ldap_users():
    """Se connecte à l'AD et récupère tous les utilisateurs humains"""
    print(f"[INFO] Connexion au serveur LDAP {LDAP_HOST}...")
    
    # Connexion simple
    server = ldap3.Server(LDAP_HOST, get_info=ldap3.ALL)
    conn = ldap3.Connection(server, LDAP_USER, LDAP_PWD, auto_bind=True)
    
    # Recherche : On veut les objets 'inetOrgPerson' dans l'unité 'ou=People'
    # On demande des attributs précis : Prénom, Nom, Description (Statut), GID (Groupe)
    conn.search('ou=People,dc=iam,dc=lab', '(objectClass=inetOrgPerson)', 
                attributes=['cn', 'givenName', 'sn', 'description', 'gidNumber'])
    
    users = []
    for entry in conn.entries:
        users.append({
            'cn': str(entry.cn),           # Nom complet
            'first': str(entry.givenName), # Prénom
            'last': str(entry.sn),         # Nom de famille
            'status': str(entry.description), # Notre champ 'Statut' (Active/Inactive)
            'gid': str(entry.gidNumber)    # ID du groupe (5000=Finance, 5001=IT)
        })
    return users

def generate_uid(first, last):
    """Règle de nommage : Première lettre prénom + Nom (ex: a.dupont)"""
    # .strip() enlève les espaces inutiles, .lower() met en minuscule
    clean_first = first.strip().lower()
    clean_last = last.strip().lower()
    return f"{clean_first[0]}.{clean_last}"

def determine_role(gid):
    """Matrice de Rôles : Convertit un Groupe technique (GID) en Rôle Business"""
    if gid == '5000': 
        return 'FINANCIAL_CONTROLLER' # Si groupe Finance
    if gid == '5001': 
        return 'IT_SUPPORT'           # Si groupe IT
    return 'USER_STANDARD'            # Par défaut


# --- C. MOTEUR DE RÉCONCILIATION (BOUCLE PRINCIPALE) ---

def reconcile():
    print("--- Démarrage du Cycle de Provisioning ---")
    
    # 1. Lecture de la Source
    try:
        users = get_ldap_users()
    except Exception as e:
        print(f"[ERREUR] Impossible de lire le LDAP : {e}")
        return

    print(f"[INFO] {len(users)} identités trouvées dans l'annuaire.")

    # 2. Traitement pour chaque utilisateur
    for u in users:
        # Calcul de l'ID unique
        uid = generate_uid(u['first'], u['last'])
        
        # CAS 1 : L'utilisateur est ACTIF -> On PROVISIONNE (Création/Mise à jour)
        if u['status'] == 'Active':
            role = determine_role(u['gid'])
            
            # Préparation des données pour l'API cible
            payload = {
                "fullname": u['cn'],
                "role": role,
                "email": f"{uid}@company.com"
            }
            
            print(f"[PROVISION] Traitement de {uid} (Rôle: {role})...")
            try:
                # Appel POST vers l'application
                r = requests.post(f"{APP_URL}/{uid}", json=payload)
                if r.status_code == 201:
                    print("   -> Succès (Compte créé/mis à jour).")
                else:
                    print(f"   -> Erreur API : {r.status_code}")
            except Exception as e:
                print(f"   -> Erreur de connexion API : {e}")

        # CAS 2 : L'utilisateur est INACTIF -> On DÉPROVISIONNE (Suppression)
        elif u['status'] == 'Inactive':
            print(f"[DE-PROVISION] Départ détecté pour {uid}. Suppression des accès...")
            try:
                # Appel DELETE vers l'application
                r = requests.delete(f"{APP_URL}/{uid}")
                if r.status_code == 200:
                    print("   -> Succès (Compte supprimé).")
                elif r.status_code == 404:
                    print("   -> Info : Le compte n'existait déjà plus.")
                else:
                    print(f"   -> Erreur API : {r.status_code}")
            except Exception as e:
                print(f"   -> Erreur de connexion API : {e}")

    print("--- Fin du Cycle ---")

if __name__ == '__main__':
    reconcile()