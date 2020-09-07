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
        if 'automated_airdrop' in f'{line}'.strip():
            print("Cron job already exists")
            break

    if 'automated_airdrop' not in f'{line}'.strip():
        job = cron.new(command='/usr/bin/python3 ~/tipbot-v2/automated_airdrop.py',
                       comment='automated_airdrop')
        job.hour.every(3)
        job.minute.on(0)
        job.enable(False)
        cron.write()
        print("Cron job created")

def enable_batch_airdrop():
    cron = CronTab(user='root')
    for job in cron:
        if job.comment == 'automated_airdrop':
            job.enable(True)
            cron.write()
            print("Enabled!")
        else:
            print("Job doesn't exist")

def disable_batch_airdrop():
    cron = CronTab(user='root')
    for job in cron:
        if job.comment == 'automated_airdrop':
            job.enable(False)
            cron.write()
            print("Disabled!")
        else:
            print("Job doesn't exist.")
