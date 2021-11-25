#!/usr/bin/env python3
from datetime import datetime, timedelta
from os import path, makedirs, getcwd, remove
import pandas as pd
import threading
import requests

# Sucuri Info
SUCURI_API_URL = "https://waf.sucuri.net/api?v2"
SUCURI_SITES = []

def daterange(start_date, end_date):    #date range generator
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def sucuri_to_disk():   #function to pull data from sucuri into disk (backup?)
    for i in SUCURI_SITES: #iterate through sites dictionaries list
        if i["enabled"]:
            try:    #try to make domain folder "*.{gob,mil}"
                makedirs('/'.join(["/mnt/cleonardo", "sucuri", i["domain"]]))
            except FileExistsError: #if it exists, pass
                pass
            for single_date in daterange(datetime.strptime(i["added_time"], "%Y-%m-%d"), datetime.now()):   #iterate from domain's "added time" until current date
                try:
                    SUCURI_FILE = '-'.join([
                        '/'.join([
                            "/mnt/cleonardo", 
                            "sucuri",
                            i["domain"],
                            i["domain"]
                        ]),
                        single_date.strftime("%Y-%m-%d"),
                        '1000'
                    ]) + '.csv'   #filename under specified domain folder, with format {directory}/{domain}/{date}.csv
                    if path.isfile(SUCURI_FILE):    #if csv file exists, pass
                        pass
                    else:   #else, make the request and write the response to the file
                        with open(SUCURI_FILE, 'w', encoding="utf-8") as f:
                            f.write(
                                requests.post(
                                    SUCURI_API_URL, # api_url
                                    data={
                                        "k": i["key"],  #domain sucuri key
                                        "s": i["secret"],   #domain sucuri secret
                                        "a": "audit_trails",    #sucuri action
                                        "date": single_date.strftime("%Y-%m-%d"),    #date
                                        "format": "csv", #data format
                                        "limit": 1000
                                    }
                                ).text  #take HTTP response body (csv file)
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
                            df["site"] = i["domain"]
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
                except:
                    continue

if __name__ == "__main__":
    try:
        makedirs('/'.join(["/mnt/cleonardo", "sucuri"]))
    except FileExistsError:
        pass
    threads = list()
    for index in range(100):
        x = threading.Thread(target=sucuri_to_disk, daemon=True)
        threads.append(x)
        x.start()
    for index, thread in enumerate(threads):
        thread.join()
