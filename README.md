# BitGreen Tipbot


### TODO
- [X] **Airdrop -> Tipbot merge** - _(prefix=$)_
    - [ ] **Airdrop commands**
      - [ ] **USER commands**
        - [ ] getinfo
        - [ ] join
        - [ ] cmd
      - [x] **ADMIN commands**
        - [x] stats
        - [x] end
        - [x] airdrop
        - [x] send
        - [x] set_retweet
        - [x] lasttx
  - [ ] **Twitter commands**
    - [x] **USER commands**
      - [x] register_airdrop
      - [x] verify
    - [ ] **ADMIN commands**
      - [ ] dfa_stats
    - [x] **ADMIN commands**
      - [x] setup_batch_cron
      - [x] enable_batch_airdrop
      - [x] disable_batch_airdrop
  
- [x] **Upgrade to Discord v1.0**
  - [x] **TipBot USER commands**
    - [x] tip
    - [x] donate
    - [x] deposit
      - [X] dlist
    - [x] withdraw
      - [x] wlist
    - [x] rain
    - [x] soak
    - [x] bet
    - [ ] guess
    - [x] coingecko
    - [ ] invite
  - [x] **TipBot ADMIN commands**
    - [x] wallet
    - [x] uptime
    - [ ] checksoak
    - [ ] allowsoak
    - [ ] log
    - [ ] pull
    
- [x] **SQL Server**
    - [ ] frequent backup of [users] table
    - [ ] test db failure i.e. disaster recovery
        - [ ] import from sql backup

- [ ] **Stress test**
    - [ ] **Transactions**
        - [x] 100 transactions ``fe96d3ccee3f17527250a58d23550bf396a6f530b146ae981e9857b5712c23f1``
        - [ ] 250 transactions
        - [ ] 500 transactions
        - [ ] 750 transactions
        - [ ] 1000 transactions
    - [ ] Heavy command load

### Future release
- [ ] **Staking**
- [ ] **QR Code on deposit address**
- [ ] **Lottery**
- [ ] **Governance**
    - [ ] Vote on future updates of the bot
- [ ] **Github integration (proof-of-code i.e. a method of validating the bot is running exactly what's on discord)**
- [ ] **Tipping integrations (tip users by @ing the bot)**
    - [ ] Twitter integration
    - [ ] Reddit integration

# Requirements
* discord.py installed
* Python 3.6+
* A MySQL database
* The BitGreen wallet w/ RPC enabled.

# Functions
* Display general wallet information
* Display individual user balances
* Store user balance information in database
* Generate new deposit addresses for users
* Automatically add users to database
* Allow users to withdraw coins from the wallet with respect to how many coins they have in the DB

# Instructions
These instructions were used to create a working bot in March 2018.
Once a VPS is obtained, follow these instructions.
## mySQL
These instructions will help you install and setup a mySQL database
### Install mySQL
```
sudo apt-get install mysql-server
```
When prompted, set up a password for root.
### Configure mySQL Security
```
mysql_secure_installation
```
Press "Y" and ENTER to accept all the questions, with the exception of the one that asks if you'd like to change the root password.
### Verify mySQL is Running
```
systemctl status mysql.service
```
You should see a status message that says "active (running)".
## Update Python
Python should be updated to version 3.6 because version 3.5 is not compatible with some libraries
```
sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt update
sudo apt-get install python3.6
sudo apt-get install python3.6-dev
sudo apt-get install python3.6-venv
```
## Install Python's pip
Python's pip is a useful tool used to install python libraries
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python3.6 get-pip.py
```
## Link python3 to python3.6
```
sudo ln -s /usr/bin/python3.6 /usr/local/bin/python3
```
## Install Discord Library
Install the discord library used for the bot
```
python3 -m pip install -U discord.py
```
## Install PyMySQL Library
```
pip install PyMySQL
```
## Clone tipbot repository
```
git clone https://github.com/denuoweb/tipbot-v2
```

## Configuration

Configure config.json

## Run bot
```
cd tipbot-v2

python3 bot.py
```
