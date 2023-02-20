# SF's Rout (SFR) - Report Downloader

## What is it?

**SFR** is a report downloader. In current form supports **SFDC** reports. The app allows you to download reports based on their ID using your personal SFDC account. Supports asynchronous requests, threaded processing of the files, logging to rotating file and stdout, produces summary report for the session. 

## Installation


- navigate to some convenient folder

```sh
cd c:/path/to/sfr
```

- clone the repo

```sh
git clone https://github.com/LukaszHoszowski/SF-s_Rout-SFR
```
- create Python virtual env

```sh
python -m venv /path/to/new/virtual/environment
```

- activate virtual env

for Windows:
```sh
c:\path\to\new\virtual\environment\Scripts\activate.bat
```

for Unix
```sh
source /path/to/new/virtual/environment/bin/activate
```

- install dependencies

```sh
pip install -r requirements.txt
```

- configure config files **./input/reports.csv** and **./.env**

- run main.py

```sh
python main.py
```

or 

```sh
python3 main.py
```

alternatively you can run main with parameter:

```sh
main.py "c:\sfr\input\reports.csv""
```

This application has been created this way that you can add this as a task to your Windows Task Schduler.

Create name.bat file in main folder of application, save it with below script

```sh
"c:\path\to\new\virtual\environment\Scripts\python.exe" "c:\path\to\clonned\repo\main.py" "c:\path\to\input\reports.csv"
pause
```

Test it, if works create a task and set some schedule

## How the program works

Once you run `main.py`:

1) loading config files
2) creating connector, report, shared queue objects
3) initialization of workers listeners within file handler
4) connector will check the connection and execute all required steps to establish the connection
5) connector will produce asynchronous requests to given domain
6) once single request if fulfilled retrieved content is being put into the queue
7) workers keep on listen for items in the queue
8) once queue is not empty some worker will take the item and start processing
9) once all the request are fulfilled queue will close and send signals to workers to shutdown once they finish their last job
10) creating summary report and saved to **./input/reports.csv**

## Connectors

At the moment the app supports only one type of reports -> SFDC

### SFDC

**Authentication:**

Authorization and authentication in SFDC is based on `sid` cookie entry for SSO or on security tokens in other cases. 

SFR will try to connect to CookieJar of your MS Edge and find `sid` entry for given domain. If `sid` is not found, the app will open MS Edge and request given SFDC domain. You will be asked to log in as usual. After 30 seconds program will retry to find `sid` in your CookieJar. Browsers usually store cookies in SQlite db, this information is not being transfer to db immediately, it can be triggered be closing but it isn't the most elegant solution. Connector will ask for `sid` in 2 seconds intervals as long as `sid` will be available. Entire process will repeat as many times as it takes.

**Sending requests:**

SFDC supports export GET requests -> `?export=csv&enc=UTF-8&isdtp=p1` supplemented with headers and above `sid` entry. In response you will receive CSV-like data stream. Time windows for entire operation is fixed and equal to **15 minutes**. If you will not be able to receive response in this time connection will be forceable shutdown and request cancelled regardless of the stage.

Requests are send out asynchronously to speed things up and restrain memory consumption to bare minimum. Once request will fail, regardless of that what has caused failure, SFR will retry. Limit of attempts has been set to **20**. Once request is successful response  is saved in Report object and put to the queue for further processing.

## File handler

Thread based solution for saving request responses to a file. At the moment only CSV files are supported.

File handler spawns workers in separate threads. Number of workers is equal to half of available threads on your machine (e.g. if your cpu has 6 cores and 12 threads SFR will spawn 6 workers). If information about available resources is not reachable it will default to **2**. Such approach will not dramatically slow down other applications on your computer and will secure required resources for SFR. Each worker will observe `Queue`, if something will be put into `Queue` one of the workers will start processing of the report. Bare in mind that each saving operation erase response and content of the report due to memory consumption. `Queue` size in unlimited so sooner or later workers will handle entire workload. Workers will die once `Queue` will send signal that they shouldn't expect any new items. These workers who are just processing items will finish their jobs and die quietly.

All files are processed by Pandas which gives wide palette of available formats.

## Limitations

- **Caution!** SFR deletes last 5 lines from each response, SFDC adds footer to each data stream. This maight be organization specific and require your attention if you plan to use it other organizations.

- by default queue is not limited

- be default number of workers in equal to half of available threads of the machine

- by default logs level for rotating file (3 part, up to 1_000_000 bytes) is set to INFO, for stdout is set to WARNING

- progress bar is based on quantity of items and my show incorrect ETA

- currently only save to CSV method is available

## Benchmarks

My testing set consist of 33 reports from various universes of SFDC with size between 200 kb to 200 mb. In total 1.4 gb of data.

Tests were not bounded by network bandwidth, at least on my side. Tests were evaluated on i7-8850H, DDR4 32 gb, Windows 10 x64.

Processing of the testing set vary between 3 and 8 minutes, results strongly correlate to SFDC performance on given time. Time of processing is correlated to size of the report.

## Final remarks

This app has been created based on environment of my organization. There is alternative way of Authenticating to SFDC based on security token, unfortunately this option was blocked in my organization and only SSO is available. 

Program has been created as efficient tool which can be hosted on relatively weak machine with limited resources. In current revision I've decreased memory footprint and distribute resources more accurately.

## Release Notes

[CHANGELOG](CHANGELOG.md)

## License

[Apache 2.0](LICENSE.md)
