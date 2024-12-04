# $reply guyz 

Here is the installation including optional steps for contributors.

## Installation 
Prepare `.env` file 
```
# CHATGPT
CHATGPT_SECRETKEY_PROJECT=

# DATABASE
DATABASE=
DB_HOST_PROD=
DB_PORT_PROD=
DB_PW=
DB_USER=

# ENVIRONMENT
ENV=

# LOCAL CONFIG
PYTHONSTARTUP=

# TELEGRAM BOT
BOT_TOKEN=
BOT_URL=
```
### Prepare installation 

## Requirements
- Ubuntu 24.04.1
 
```shell
sudo apt update
sudo apt install \
    ca-certificates \
    curl \
    gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

git clone git@github.com:0Follows1Dream/reply_guyz.git # clone the repo 
cd reply_guyz # enter directory 
touch .env
chmod +x /startup/local/load_env_vars.sh # automate the loading of env vars from .env 
source ./startup/local/load_env_vars.sh # load the env vars into current shell 
sudo docker compose up --build -d # builder the docker container in detached mode 
```


### Disclaimer: 

No financial strings attached, just vibes. Zenon lore, reply guyz and vibes. 

This project is an example design for a community-focused awareness campaign featuring a reputation/social token system (like in-game points). It's a journey.  

_Please keep the following in mind:_  

**Vibes:** Enjoy the campaign for what it is—a chance to vibe, interact and develop with the community. 

**Purpose:** 
The \$REPLY token is designed for fun, community engagement, and participation within the Zenon ecosystem. It has no financial value, is not tradable, and should not be considered an investment.  

**No Guarantees:** This code is provided "as is" without any warranties or guarantees. Use or adapt it as you see fit, but at your own risk.  

**For Illustration Only:** This code is intended as an example and is not ready for direct deployment. Further development, security measures, and customisation by qualified professionals are needed before any real-world use.  

**No Liability:** The author is not responsible for how this code is used or adapted.    

**Not Financial or Technical Advice:** This is not financial or technical advice. Cryptocurrency projects are highly risky and speculative. You may lose all your invested capital. Approach thoughtfully and responsibly.    

**Your Responsibility:** If you adapt this code, you are responsible for ensuring it meets all technical, security, and regulatory requirements, especially if $REPLY or similar tokens are used in other contexts.  