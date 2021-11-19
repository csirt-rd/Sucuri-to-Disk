#!/usr/bin/env python3
from datetime import datetime, timedelta
from os import path, makedirs, getcwd
import pandas as pd
import threading
import requests

# Sucuri Info
SUCURI_API_URL = "https://waf.sucuri.net/api?v2"
SUCURI_SITES = []

LOG_FILE = '-'.join([
    '/'.join([getcwd(), 'logs', 'log']),
    datetime.now().strftime("%Y%m%d")
]) + '.txt'

def daterange(start_date, end_date):   
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def sucuri_to_disk(name):  
    for i in SUCURI_SITES:
        if i["enabled"]:
            try:   
                makedirs('/'.join([getcwd(), 'logs']))
            except FileExistsError:
                pass
            try:   
                makedirs('/'.join([getcwd(),i["domain"]]))
            except FileExistsError:
                pass
            for single_date in daterange(datetime.strptime(i["added_time"], "%Y-%m-%d"), datetime.now()):  
                mutex.acquire()
                SUCURI_FILE = '-'.join([
                    '/'.join([
                        getcwd(),
                        i["domain"],
                        i["domain"]
                    ]),
                    single_date.strftime("%Y-%m-%d"),
                    '1000'
                ]) + '.csv'  
                if path.isfile(SUCURI_FILE):   
                    pass
                else:  
                    with open(LOG_FILE, 'a', encoding='utf-8') as l:
                        l.write(
                            ' '.join([
                                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3],
                                '+00:00',
                                '[INF]',
                                'Getting 1000 logs from',
                                i["domain"],
                                'at',
                                single_date.strftime("%Y-%m-%d"),
                                '\n'
                            ])
                        )
                    l.close()  
                    with open(SUCURI_FILE, 'w', encoding="utf-8") as f:
                        f.write(
                        requests.post(
                            SUCURI_API_URL,
                            data={
                                "k": i["key"], 
                                "s": i["secret"],  
                                "a": "audit_trails",   
                                "date": single_date.strftime("%Y-%m-%d"),   
                                "format": "csv",
                                "limit": 1000
                            }
                        ).text 
                    )
                    f.close()
                    try:
                        df = pd.read_csv(SUCURI_FILE)
                    except:
                        pass
                    else:
                        df["site"] = i["domain"]
                        df["request_date"] = single_date.strftime("%d-%b-%Y")
                        df["request_time"] = datetime.now().strftime("%H:%M:%S")
                        df.to_csv(SUCURI_FILE, index=False)
                    with open(LOG_FILE, 'a', encoding='utf-8') as l:
                        l.write(
                            ' '.join([
                                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S:%f")[:-3],
                                '+00:00',
                                '[INF]',
                                'Saving',
                                '-'.join([i["domain"], single_date.strftime("%Y-%m-%d"), '1000']) + '.csv',
                                'to disk',
                                '\n'
                            ])
                        )
                    l.close()  
                mutex.release()

if __name__ == "__main__":
    mutex = threading.Lock()
    threads = list()
    for index in range(50):
        x = threading.Thread(target=sucuri_to_disk, args=(index,), daemon=True)
        threads.append(x)
        x.start()
    for index, thread in enumerate(threads):
        thread.join()
