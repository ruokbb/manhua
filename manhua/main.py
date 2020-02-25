
import sched
import time
import os
schedule = sched.scheduler(time.time,time.sleep)

def func():
    os.system('scrapy crawl search_all')

def func2(inc):
    schedule.enter(inc,0,func2,(inc,))
    func()

if __name__ == '__main__':
    schedule.enter(0,0,func2,(21600,))
    schedule.run()