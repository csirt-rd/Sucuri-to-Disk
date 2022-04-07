#!/usr/bin/env python3
import threading, requests
import pandas as pd
from datetime import datetime, timedelta
from os import path, makedirs, remove

# Sucuri Info
SUCURI_API_URL = "https://waf.sucuri.net/api?v2"
SUCURI_API_KEY = "..."
SUCURI_SITES = [
    ...
]

#Sucuri to Disk
def sucuri_to_disk(domain, key, secret, date):
    try:
        makedirs('/'.join([getcwd(), "sucuri", domain]))
    except FileExistsError:
        pass
    finally:
        SUCURI_FILE = '-'.join([
            '/'.join([
                getcwd(),
                "sucuri",
                domain,
                domain
            ]),
            date.strftime("%Y-%m-%d"),
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
                            "date": date.strftime("%Y-%m-%d"),
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
                df["request_date"] = date.strftime("%d-%b-%Y")
                df["request_time"] = datetime.now().strftime("%H:%M:%S")
                try:
                    df = df.drop(columns="geo_location")
                except KeyError:
                    df = df[df.is_usable != 0]
                    df.to_csv(SUCURI_FILE, index=False)
                else:
                    df = df[df.is_usable != 0]
                    df.to_csv(SUCURI_FILE, index=False)

if __name__ == "__main__":
    try:
        makedirs('/'.join([getcwd(), "sucuri"]))
    except FileExistsError:
        pass
    finally:
        yesterday = datetime.now() - timedelta(1)
        threads = list()
        for i in SUCURI_SITES:
            data = requests.post(
                SUCURI_API_URL,
                data={
                    "k": SUCURI_API_KEY,
                    "s": i['secret'],
                    "a": "show_settings"
                }
            ).json()
            i['enabled'] = True if data['output']['proxy_active'] == 1 else False
            i['domain'] = data['output']['domain']
            i['key'] = SUCURI_API_KEY
            if i["enabled"]:
                x = threading.Thread(
                    target=sucuri_to_disk,
                    args=(
                        i["domain"],
                        i["key"],
                        i["secret"],
                        yesterday
                    ), daemon=True
                )
                threads.append(x)
                x.start()
        for index, thread in enumerate(threads):
            thread.join()
