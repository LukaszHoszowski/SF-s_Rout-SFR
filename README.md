## SF's Rout (SFR) - Report Downloader

## What is it?

**SFR** is a report downloader. In current form supports **SFDC** reports. The app allows you to download reports based on their ID using your personal SFDC account. Supports asynchronous requests, threaded processing of the files, logging to rotating file and stdout, produces summary report for the session. 

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

- activate virtual env

for Windows:
```sh
/path/to/new/virtual/environment\Scripts\activate.bat
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

## Limitations

- by default queue is not limited

- be default number of workers in equal to half of available threads of the machine

- by default logs level for rotating file (3 part, up to 1_000_000 bytes) is set to DEBUG, for stdout is set to WARNING

- progress bar is based on quantity of items and my show incorrect ETA

- currently only save to CSV method is available

## Benchmarks

My testing set consist of 33 reports from various universes of SFDC with size between 200 kb to 200 mb. In total 1.4 gb of data.

Tests were not bounded by network bandwidth, at least on my side. Tests were evaluated on i7-8850H, DDR4 32 gb, Windows 10 x64.

Processing of the testing set vary between 3 and 8 minutes, results strongly correlate to SFDC performance on given time. Time of processing is correlated to size of the report.

## Final remarks

This app has been created based on environment of my organization. There is alternative way of Authenticating to SFDC based on security token, unfortunately this option was blocked in my organization and only SSO is available. 

Program has been created as efficient tool which can be hosted on relatively weak machine with limited resources. I current revision I've decreased memory footprint and distribute resources more accurately.

## Release Notes
[CHANGELOG](CHANGELOG.md)

## License
[Apache 2.0](LICENSE.md)
