![GitHub Logo](https://i.imgur.com/TJGzhQo.png)
# Crypto Tipbot
#### Requirements
* Discord.py installed
* Python 3.6+
* MySQL database
* BitGreen wallet w/ RPC enabled.

#### Functions
* Display general wallet information
* Display individual user balances
* Store user balance information in database
* Generate new deposit addresses for users
* Automatically add users to database
* Allow users to withdraw coins from the wallet with respect to how many coins they have in the DB
* Initiate airdrop where the user can participate by retweeting the specified tweet; this is to help towards social awareness/coin distribution

#### Wallet settings
* txfee = **_0.00001000_**
* withdraw fee = **_0.005_**
* minimum withdrawal = **_0.009_**
* minimum confirmation = **_2_**

---

## Tested environment 
#### System specification
* Ubuntu 18.04+
* 1 vCore
* 1024MB RAM
#### Setting up a 2GB swap file
```sh
dd if=/dev/zero of=/swapfile count=2048 bs=1M
```
#### Activate/Turn the swap file on
```sh
chmod 600 /swapfile
ls -lh /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## Prerequisites
#### Wallet config
```
rpcbind=127.0.0.1
rpcport=8331
rpcuser=<USERNAME>
rpcpassword=<PASSWORD>
staking=0
rpcworkqueue=512
```

#### Python libraries
```sh
apt install python3-pip  
pip3 install python-crontab  
pip3 install discord.py  
pip3 install python-dateutil  
pip3 install PyMySQL

git clone https://github.com/Nadro-J/tweepy.git
cd tweepy
python3 setup.py install
```

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

> ##### Uninstall/Remove MySQL _(only required if anything breaks and you want to start the SQL server from scratch)_
>> sudo apt-get remove --purge mysql*  
sudo apt-get purge mysql*  
sudo apt-get autoremove  
sudo apt-get autoclean  
sudo apt-get remove dbconfig-mysql  
sudo apt-get install mysql-server  

#### Creating SQL user, setting permissions for daily backups
```sql
CREATE USER 'tipbot'@'localhost' IDENTIFIED BY 'SECUREP455W0RD';
CREATE DATABASE IF NOT EXISTS DiscordTipBot;
GRANT ALL ON mysql.* TO 'tipbot'@'localhost';
GRANT ALL ON DiscordTipBot.* TO 'tipbot'@'localhost';
GRANT SELECT, PROCESS ON *.* TO 'tipbot'@'localhost';
FLUSH PRIVILEGES;
```

#### Cronjob MySQL hourly backup
```
crontab -e
0 * * * * ~/tipbot-v2/setup/data/mysql_backup.sh > ~/tipbot-v2/logs/mysql_backup.log 2>&1
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