# Changelog

All notable changes to this project will be documented in this file.

## [0.1.3] - 2023-02-24
### Added
- new class -> Config has been added

### Changed
- logic separation between components
- everything related to configuration moved to Config
- documentation

## [0.1.2] - 2023-02-21
### Added
- CLI params handling by Click

### Changed
- error handling in requests
- logging support
- readme
- some organizational changes to internal structure

## [0.1.1] - 2023-02-18
### Added
- Logging module
- TQDM progress bar
- Paths handling
- CHANGELOG added

### Changed
- entire engine has been replaced with asynchronous requests
- file handling process is now threaded
- huge memory footprint has been elimnated
- entire internal organization of the program has been improved to more logical structure
- logic separation in connectors, saving the files has been moved to FileHandler
- typing improvements
- legacy prgress bar has been retired and replaced with TQDM solution
- defaults for config file and their names
- README updated

### Fixed
- fails handling of requests improved, time to time request wasn't repeated when failed
- memory footprint, resources management in general

## [0.0.1] - 2023-02-14
### Initial release
- Initial release of `SFR` based on multiprocessing