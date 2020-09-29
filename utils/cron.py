from crontab import CronTab
from datetime import datetime

def schedule():
    cron = CronTab(user='root')
    for job in cron:
        sched = job.schedule(date_from=datetime.now())
        return sched.get_next()

def create_cronjob():
    cron = CronTab(user='root')

    for line in cron.lines:
        line = line
        if 'auto_airdrop' in f'{line}'.strip():
            return "Cron job already exists"
            break

    if 'auto_airdrop' not in f'{line}'.strip():
        job = cron.new(command='/usr/bin/python3 ~/tipbot-v2/auto_airdrop.py > ~/tipbot-v2/logs/auto_output.log 2>&1', comment='auto_airdrop')
        job.hour.every(3)
        job.minute.on(0)
        job.enable(False)
        cron.write()
        return "Cron job created"

def enable_batch_airdrop():
    cron = CronTab(user='root')
    for job in cron:
        if job.comment == 'auto_airdrop':
            job.enable(True)
            cron.write()
            return "Enabled!"
        else:
            return "Job doesn't exist"

def disable_batch_airdrop():
    cron = CronTab(user='root')
    for job in cron:
        if job.comment == 'auto_airdrop':
            job.enable(False)
            cron.write()
            return "Disabled!"
        else:
            return "Job doesn't exist."
