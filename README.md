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


#### Disclaimer: 
- This code showcases an example design for an incentivised awareness campaign with an earning component of a reputation/social token similar to ingame points that aren't tradeable or used for investment purposes.
- The code is provided as is and the writer does not accept liability for any users choosing to use or adapt this code.
- This campaign and the $REPLY token are designed solely for community engagement and narrative development.
- $REPLY has no financial value, is not an investment, and is only meant for use within the Zenon awareness campaign ecosystem as a social reward for participation.
- Zenon encourages all users to approach the campaign for fun and interaction, without financial expectations.
- This is not financial or technical advice. Crypto is very risky and you may lose all your invested capital.  
- The code is intended purely as an illustrative example and is not intended for direct deployment without further development, security measures, and customisation by qualified personnel.
- Any parties adapting this code are responsible for conducting their own technical, security, and regulatory review, especially if $REPLY or similar tokens are introduced in other contexts. 