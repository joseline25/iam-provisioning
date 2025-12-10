Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/focal64" # Ubuntu 20.04

  # --- VM 1 : ANNUAIRE (Source) ---
  config.vm.define "iam-ldap" do |ldap|
    ldap.vm.hostname = "iam-ldap"
    ldap.vm.network "private_network", ip: "192.168.56.10"
    ldap.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.name = "IAM-Lab-LDAP"
    end
    # Installation silencieuse de OpenLDAP
    ldap.vm.provision "shell", inline: <<-SHELL
      export DEBIAN_FRONTEND=noninteractive
      apt-get update
      # On définit le mot de passe admin à 'admin' pour l'installation auto
      echo "slapd slapd/root_password password admin" | debconf-set-selections
      echo "slapd slapd/root_password_again password admin" | debconf-set-selections
      apt-get install -y slapd ldap-utils
    SHELL
  end

  # --- VM 2 : APPLICATION CIBLE (Target) ---
  config.vm.define "iam-app" do |app|
    app.vm.hostname = "iam-app"
    app.vm.network "private_network", ip: "192.168.56.20"
    app.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.name = "IAM-Lab-APP"
    end
    app.vm.provision "shell", inline: <<-SHELL
      apt-get update
      apt-get install -y python3-pip
      pip3 install flask
    SHELL
  end

  # --- VM 3 : CONTROL CENTER (Moteur IAM) ---
  config.vm.define "iam-control" do |ctl|
    ctl.vm.hostname = "iam-control"
    ctl.vm.network "private_network", ip: "192.168.56.30"
    ctl.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.name = "IAM-Lab-Control"
    end
    ctl.vm.provision "shell", inline: <<-SHELL
      apt-get update
      apt-get install -y python3-pip ldap-utils curl
      pip3 install ldap3 requests
      # On aide la machine à trouver les autres par leur nom
      echo "192.168.56.10 iam-ldap" >> /etc/hosts
      echo "192.168.56.20 iam-app" >> /etc/hosts
    SHELL
  end
end