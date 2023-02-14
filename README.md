## SF's Rout (SFR) - Report Downloader

## What is it?

**SFR** is a report downloader for **SFDC**. The app allow you to download retports based on their ID using your personal SFDC account. Supports multiprocessing of the requestes, loads the data to csv containair, produce summary report for the session. 

## Installation

- navigate to some convenient folder

- clone the repo

```sh
git clone https://github.com/LukaszHoszowski/SF-s_Rout-SFR
```
- create Python virtual env

```sh
python -m venv /path/to/new/virtual/environment
```
 
- install dependencies

```sh
pip install -r requirements.txt
```

- fill in config files **/input/sfdc_reports.csv** and **/.env**

## How the program works

Once you run `main.py`:

1) The app will read config files.
2) Next, the app will review CookieJar of your MS Edge browser looking for SID of SFDC session. SFDC allows to download the reports through GET requests but you need to be logged in. Entire Authorization process is based on Cookie entry called SID. Program will try to intercept the SID value and use it in request.
3) ? If SID is not present Program will invoke MS Edge to request SFDC domain in order to log in. Once you will log in the SID entry will be created and saved in local CookieJar database. After 30 sec SFR will try to intercept the value of newly created SID entry directly from DB.
4) ? If SID is present, the App will execute check procedure. Program will try to reach SFDC domain, if SID is fine, aproperiate message will be printed.
5) ? If self check fails Program will circle back to point no 3 and will execute SID interception procedure and repeat check. SID is a Session Cookie entry so it might expire with time and needs to be renewed before we will proceed further.
6) If all the lights are green Connector will create a list of report objects based on config file. 
7) Next, reports will be distributed to independant processes and will be downloaded in parallel. Everything is orchestrated by Manager.
8) ? If for some reasons the App will fail with some of the reports entire process will be reapeated for them to be sure that all requested reports are downloaded. There is no hard limit of number of attempts. Information about number of tries will be recorded.
9) Finally, reports will be saved to CSV.
10) Summary report will be produced.

## Final remarks

The APP is not perfect. Has been created based on environment of my organisation. There is alternative way of Authenticating to SFDC based on security token, unfortunately this option was blocked in my org. 

I've decided to use multiprocessing only due to my incompetence in async :>, maybe not only because of that. I'm using Pandas to translate binary to csv, Pandas do not like async. To do not overcomplicate internals i've decided to stick with one parallel solution. Ideally it should be combination of async for requests and threading for pandas or csv. However i had some difficulties with async requests. Many decssion to make, to little time to implement all of the options. I decided to stick with what i know and feel confortable with. This for sure can be improved. Scrint is running on relatively strong machine so i wasn't bounded by performance. Yes, Pandas might look like an overkill here but I usually do data cleansing after download so it's handy. 

## License
[Apache 2.0](LICENSE.md)
