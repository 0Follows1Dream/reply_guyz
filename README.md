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
```shell
git clone ... # clone the repo 
cd reply_guyz # enter directory 
chmod +x /scripts/load_env_vars # automate the loading of env vars from .env 
source ./startup/load_env_vars # load the env vars into current shell 
docker-compose up -d --build # builder the docker container in detached mode 
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