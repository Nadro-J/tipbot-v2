![GitHub Logo](https://i.imgur.com/TJGzhQo.png)
# Crypto Tipbot
#### Requirements
* Discord.py installed
* Python 3.6+
* MySQL database
* The BitGreen wallet w/ RPC enabled.

#### Functions
* Display general wallet information
* Display individual user balances
* Store user balance information in database
* Generate new deposit addresses for users
* Automatically add users to database
* Allow users to withdraw coins from the wallet with respect to how many coins they have in the DB
* Initiate airdrop where the user can participate by retweeting the specified tweet; this is to help towards social awareness/coin distribution
---
## Prerequisites
#### MySQL
These instructions will help you install and setup a mySQL database
#### Install MySQL
```
sudo apt-get install mysql-server
```
When prompted, set up a password for root.

#### Configure MySQL Security
```
mysql_secure_installation
```
Press "Y" and ENTER to accept all the questions, with the exception of the one that asks if you'd like to change the root password.

#### Verify mySQL is Running
```
systemctl status mysql.service
```
You should see a status message that says "active (running)".

#### Creating SQL user, setting permissions for daily backups
```sql
CREATE USER 'tipbot'@'localhost' IDENTIFIED BY 'SECUREP455W0RD';
GRANT ALL ON mysql.* TO 'tipbot'@'localhost';
GRANT ALL ON DiscordTipBot.* TO 'tipbot'@'localhost';
GRANT SELECT, PROCESS ON *.* TO 'tipbot'@'localhost';
FLUSH PRIVILEGES;
```

#### Install Python's pip
Python's pip is a useful tool used to install python libraries
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python3.6 get-pip.py
```

#### Install Discord Library
Install the discord library used for the bot
```
python3 -m pip install -U discord.py
```

### Install PyMySQL Library
```
pip3 install PyMySQL
```

---

## Debugging/PM2 Setup
```
git clone https://github.com/Nadro-J/tipbot-v2.git
cd tipbot-v2/
python3 bot.py
```

---

## Future development
- [ ] **Staking**
- [ ] **QR Code on deposit address**
- [ ] **Lottery**
- [ ] **Governance**
- [ ] **Github integration (proof-of-code i.e. a method of validating the bot is running exactly what's on Github)**
- [ ] **Tipping integrations (tip users by @ing the bot)**
    - [ ] Twitter integration
    - [ ] Reddit integration