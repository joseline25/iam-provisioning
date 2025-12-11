#  IAM Provisioning Lab : Architecture Hybride Automatisée

##  Présentation
Ce projet est un démonstrateur technique (POC) illustrant la gestion du cycle de vie des identités (**Identity Lifecycle Management**) dans un environnement distribué. 

L'objectif est de simuler une chaîne de provisionnement complète : de la source de vérité (HR/Directory) vers une application cible (SaaS), en appliquant des règles de gestion (RBAC) et de nettoyage de données.

##  Architecture
L'infrastructure repose sur 3 machines virtuelles interconnectées via un réseau privé, déployées via **Vagrant** (Infrastructure as Code) :

| Rôle | Serveur | Technologie | Description |
| :--- | :--- | :--- | :--- |
| **Source** | `iam-ldap` | **OpenLDAP** | Simule l'Active Directory (Source of Truth). Contient les identités et groupes. |
| **Cible** | `iam-app` | **Python/Flask** | Simule une application SaaS (Target System) exposant une API REST. |
| **Moteur** | `iam-control`| **Python** | Héberge le moteur de réconciliation et les règles métiers. |

##  Fonctionnalités Démontrées (JML)

### 1. Joiner (Embauche)
* Détection automatique des nouveaux utilisateurs dans l'annuaire LDAP.
* Génération d'identifiants uniques (nettoyage, standardisation).
* Création du compte via API sur l'application cible.

### 2. Mover (Mobilité & RBAC)
* Calcul automatique des rôles applicatifs basé sur l'appartenance aux groupes LDAP.
* *Règle Métier :* Si `MemberOf = Finance` -> `Role = FINANCIAL_CONTROLLER`.

### 3. Leaver (Départ)
* Détection du statut "Inactive" dans la source.
* Déprovisionnement automatique (suppression) du compte sur l'application cible pour garantir la sécurité.

##  Stack Technique
* **Langage :** Python 3.8+
* **Librairies Clés :** `ldap3` (Protocole LDAP), `requests` (API Rest), `logging`.
* **Infrastructure :** Vagrant, VirtualBox, Ubuntu 20.04 LTS.
* **Services :** Systemd (Service Linux), Cron (Planification).

##  Installation & Usage

1. **Déploiement de l'infra :**
   ```bash
   vagrant up
   ```

2. **Connexion au contrôleur**
   ```bash
   vagrant ssh iam-control
   ```

3. **Exécution du moteur de synchronisation**
   ```bash
   python3 provisioning_engine.py
   ```

```mermaid
flowchart TD
    %% Définition des Styles
    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef engine fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef target fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef network stroke-dasharray: 5 5, fill:none, stroke:#999;

    subgraph VagrantHost [Ordinateur Hôte / Vagrant VirtualBox]
        direction LR

        %% VM 1 : SOURCE
        subgraph VM_LDAP [VM 1: iam-ldap]
            direction TB
            IP1(IP: 192.168.56.10)
            LDAP_DB[("🗄️ OpenLDAP\n(Port 389)")]
            Users1(Users: Alice, Bob)
            Groups1(Groups: Finance, IT)
        end
        class VM_LDAP source

        %% VM 3 : MOTEUR (CONTROL)
        subgraph VM_CTL [VM 3: iam-control]
            direction TB
            IP3(IP: 192.168.56.30)
            Cron((⏰ Cron\nEvery 1 min))
            Script["🐍 provisioning_engine.py\n(Python Script)"]
            Logs["📄 iam_sync.log"]
        end
        class VM_CTL engine

        %% VM 2 : CIBLE
        subgraph VM_APP [VM 2: iam-app]
            direction TB
            IP2(IP: 192.168.56.20)
            API["⚙️ Flask API\n(Port 5000)"]
            Systemd(Service: dummy-app)
            AppDB[("💾 In-Memory DB")]
        end
        class VM_APP target

        %% FLUX DE DONNÉES (LES FLÈCHES)
        
        %% 1. Trigger
        Cron -->|Déclenche| Script

        %% 2. Lecture (Reconciliation)
        Script -- "1. LDAP Search (Read)" --> LDAP_DB
        
        %% 3. Logique
        Script -->|Logique Métier & Transformation| Script

        %% 4. Provisioning
        Script -- "2. REST POST / DELETE (Write)" --> API

        %% 5. Logging
        Script -.->|Audit Trail| Logs

        %% Liaisons internes VM
        LDAP_DB --- Users1
        LDAP_DB --- Groups1
        Systemd --- API
        API --- AppDB

    end
```

