# Deploy Flask API

## Ubuntu Configuration

Connect via ssh to your server
* `ssh root@<server-ip>`

 Set up basic connfigs such as host name. Update operating system packages , etc...
* `apt update && apt upgrade`

* Set a `server-name` for your server and add it to the `/etc/hosts` file:
    1. `hostnamectl set-hostname <server-name>`
    2. `vi /etc/hosts`
    3. Add at the bottom `<server-ip>    <your-server-name>`

* Create a new user and add him to the sudo group
    1. `adduser <username>` and set the `<password>`
    2. `adduser <username> sudo`
 
* Logout by typing `exit` and connect back using the new `<username>`
* `ssh <username>@<server-ip>`

* Set up ssh authentication:
    1. Go to your home directory by typing `cd /`
    2. `mkdir .ssh`


* Return to your computer to create the ssh key:
    1. `ssh-keygen -b 4096`
    2. Move the public key `id_rsa.pub` the server
        1. `scp ~/.ssh/pub_rsa.pub <username>@<server-ip>:~/.ssh/authorized_keys` 


* Return to the Server to update some permissions:
    1. `sudo chmod 700 ~/.ssh/`
    2. `sudo chmod 600 ~/.ssh/*`

* Disallow root login over ssh and ssh over password:
    1. `sudo vi /etc/ssh/sshd_config`
    2. Change `PermitRootLogin yes` to `PermitRootLogin no`
    3. Change `#PasswordAuthentication yes` to `PasswordAuthentication no`
    4. `sudo systemctl restart sshd`
 
* Install and setup a Firewall:
    1. `sudo apt install ufw`
    2. `sudo ufw default allow outgoing`
    3. `sudo ufw default deny incoming`
    4. `sudo ufw allow ssh`
    5. `sudo ufw allow <development-flask-port>`
    6. `sudo ufw deny http/tcp`
    7. `sudo ufw enable`
    8.  Check what's up `sudo ufw status`

## Flask Configuration

* Return to the local machine to create the `requirements.txt` file with all the project dependencies and copy to the server
    1. `pip freeze > <project-folder>/requirements.txt`
    2. `scp -r <project-folder> <username>@<server-ip>:~/<remote-project-folder>` 

* Go to the server via `ssh <username>@<server-ip>`:
    1. `cd <remote-project-folder>`
    2. `sudo apt install python3-pip`
    3. `sudo apt install python3-venv`
    4. `python3 -m venv venv`
    5. `source venv/bin/activate`
    6. `pip install -r requirements.txt`
     
* Test everything is working fine:
    1. `python main.py`
    2. Stop the process `ctrl+c`

* Install and configure a webserver to handle incoming requests
    1. `sudo apt install nginx`
    2. Remove nginx default configuration `sudo rm /etc/nginx/sites-enabled/default`
    3. create a new config file `sudo vi /etc/nginx/sites-enabled/<project-name>`
    4. Copy this content:

```
server {
    listen 80;
    server_name <server-ip>;
  
    location / {
        proxy_pass http://localhost:<production-flask-port>;
        include /etc/nginx/proxy_params;
        proxy_redirect off;
    }
}
```

* Change firewall configurations:
    1. `sudo ufw allow <production-flask-port>`
    2. `sudo ufw deny <development-flask-port>`
    3. `sudo ufw enable`
    4. `sudo systemctl restart nginx`

* Install a python wsgi production server (Inside the venv):
    1. `cd <remote-project-folder>`
    2. `pip install gunicorn`
    3. Test the server by typing `gunicorn -w 3 -b 0.0.0.0:<production-flask-port> --timeout 120 --log-level debug main:app`
    4. Stop the process `ctrl+c`

* Config the gunicorn to run as a systemd service:
    1. `sudo cp <remote-project-folder>/<project-name>.service /etc/systemd/system/`
    2. `sudo systemctl enable <project-name>`
    3. `sudo systemctl start <project-name>`
    4. To update the *.service file:
        1. `sudo cp <remote-project-folder>/<project-name>.service /etc/systemd/system/`
        2. `sudo systemctl daemon-reload`
        3. `sudo systemctl restart <project-name>`


## At this point you are done. How ever there is a usefull configuration:

* Change nginx default files size limit from 2Mb to whatever you want:
    1. `sudo vi /etc/nginx/nginx.conf`
    2. Inside the http section include `client_max_body_size 5M;`
    3. `sudo systemctl restart nginx`
    
    
* Check venv creation:
    1. `export LC_ALL="en_US.UTF-8"`
    1. `export LC_CTYPE="en_US.UTF-8"`
    3. `sudo dpkg-reconfigure locales`

* Create the venv environment:
    1. `python3.6 -m venv venv --without-pip`
    2. `source venv/bin/activate`
    3. `cd venv/`
    4. Install pip via `curl https://bootstrap.pypa.io/get-pip.py | python3`

* Test if there is a process using the ports:
    1. `sudo lsof -i tcp:<port>`
    2. `kill -9 <process-id>`

## Using the supervisor program:

* Make the server run as a background process with autorestart:
    1. `sudo apt install supervisor`
    2. `sudo vi /etc/supervisor/conf.d/<project-name>.conf`
    3. copy this content

```
[program:<project-name>]
directory=<remote-project-folder>
command=<remote-project-folder>/venv/bin/gunicorn -w 3 -b 0.0.0.0:<production-flask-port> --timeout 120 --log-level debug main:app
user=<username>
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/<project-name>/<project-name>.err.log
stdout_logfile=/var/log/<project-name>/<project-name>.out.log
```

* Create the log files:
    1. `sudo mkdir -p /var/log/<project-name>`
    2. `sudo touch /var/log/<project-name>/<project-name>.out.log`
    3. `sudo touch /var/log/<project-name>/<project-name>.err.log`

* Restart the supervisor process:
    1. `sudo supervisorctl reread`
    2. `sudo supervisorctl update`
    3. `sudo supervisorctl restart <project-name>`
