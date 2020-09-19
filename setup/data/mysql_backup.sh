#!/bin/bash

export PATH=/bin:/usr/bin:/usr/local/bin
TODAY=`date +"%d%b%Y-%H:%M:%S"`

################################################################
################## Update below values #########################
DB_BACKUP_PATH='/backup/tipbot-sqldump'
MYSQL_HOST='localhost'
MYSQL_PORT='3306'
MYSQL_USER=''
MYSQL_PASSWORD=''
DATABASE_NAME='mysql'
BACKUP_RETAIN_DAYS=7 ## Number of days to keep local backup copy
#################################################################


mkdir -p ${DB_BACKUP_PATH}/${TODAY}
echo "Backup started for database - ${DATABASE_NAME}"

mysqldump -h ${MYSQL_HOST} \
   -P ${MYSQL_PORT} \
   -u ${MYSQL_USER} \
   -p${MYSQL_PASSWORD} \
   ${DATABASE_NAME} | gzip > ${DB_BACKUP_PATH}/${TODAY}/${DATABASE_NAME}-${TODAY}.sql.gz

if [ $? -eq 0 ]; then
  echo "Database backup successfully completed"
else
  echo "Error found during backup"
  exit 1
fi


##### Remove backups older than {BACKUP_RETAIN_DAYS} days  #####
DBDELDATE=`date +"%d%b%Y" --date="${BACKUP_RETAIN_DAYS} days ago"`

if [ ! -z ${DB_BACKUP_PATH} ]; then
      cd ${DB_BACKUP_PATH}
      if [ ! -z ${DBDELDATE} ] && [ -d ${DBDELDATE} ]; then
            rm -rf ${DBDELDATE}
      fi
fi