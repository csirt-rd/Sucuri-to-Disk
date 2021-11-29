#!/usr/bin/env python3
from datetime import datetime, timedelta
from os import path, makedirs, getcwd, remove
import threading
import pandas as pd
import requests

# Sucuri Info
SUCURI_API_URL = "https://waf.sucuri.net/api?v2"
SUCURI_SITES = []

#Date generator function
def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

#Sucuri to Disk
def sucuri_to_disk(domain, key, secret, added_time, enabled):
    if enabled:
        try:
            makedirs('/'.join([getcwd(), "sucuri", domain]))
        except FileExistsError:
            pass
        for single_date in daterange(datetime.strptime(added_time, "%Y-%m-%d"), datetime.now()):
            SUCURI_FILE = '-'.join([
                '/'.join([
                    getcwd(), 
                    "sucuri",
                    domain,
                    domain
                ]),
                single_date.strftime("%Y-%m-%d"),
                '1000'
            ]) + '.csv'
            if not path.isfile(SUCURI_FILE):
                with open(SUCURI_FILE, 'w', encoding="utf-8") as f:
                    f.write(
                        requests.post(
                            SUCURI_API_URL,
                            data={
                                "k": key,
                                "s": secret,
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
                except (pd.errors.EmptyDataError, pd.errors.ParserError):
                    try:
                        remove(SUCURI_FILE)
                    except FileNotFoundError:
                        pass
                except FileNotFoundError:
                    pass
                else:
                    df["request_date"] = single_date.strftime("%d-%b-%Y")
                    df["request_time"] = datetime.now().strftime("%H:%M:%S")
                    df["site"] = domain
                    try:
                        df = df.drop(columns="geo_location")
                    except KeyError:
                        try:
                            remove(SUCURI_FILE)
                        except FileNotFoundError:
                            pass
                    else:
                        df = df[df.is_usable != 0]
                        df.to_csv(SUCURI_FILE, index=False)

if __name__ == "__main__":
    try:
        makedirs('/'.join([getcwd(), "sucuri"]))
    except FileExistsError:
        pass
    threads = list()
    for i in SUCURI_SITES:
        x = threading.Thread(target=sucuri_to_disk, args=(i["domain"],i["key"],i["secret"],i["added_time"],i["enabled"]), daemon=True)
        threads.append(x)
        x.start()
    for index, thread in enumerate(threads):
        thread.join()
