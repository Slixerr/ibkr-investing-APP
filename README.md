# Application for the traceability of operations IBKR-Investing

In this project is detailed the creation of an application for the traceability of operations which migrates every day the data form Interactive Brokers to Investing.com creating 3 portfolios:
- First portfolio: contains al the open shares.
- Second porfolio: for long operations.
- Third portfolio: for short operations.

The objective of this programm is to simplify the monitoring of operations in the day to day life of an investor.

## Prerequisites

You must have installed and downloaded this elements before continuing and starting the application:
  * Python 
  * Trader Workstation from IBKR
  * Clone this project
  * Have an account in Investing and Interactive Brokers

# Build process

1) One of the first steps is configuring the Trader Workstation platform:
   * Access File -> Global Configuration -> API -> Configuration
   * Check "Activate clients ActiveX and Socket"
   * Check Soket Port is 7497
   * Unmark "API only read"
   * Save changes

2) Open "userCredentials.txt" and update the information to your accounts

### Windows

3) Create a periodical event in your system 
   * Set a descriptive name
   * In Windows access Scheduled Task Wizard creating a new daily task to the desired schedule.
   * Select "Start a program" option.
   * In the last section you must specify the folders:
     * Path to python.exe
     * Argument: "scriptTask.py"
     * Path for the previous directory parent folder
  *  Confirm

### Linux

3) Create a periodical event in your system - LINUX
   * Access in a terminal "crontab -e" in order to change task schedules
   * Write "MIN HOUR * * * *  python3 path_to_file"

### MacOS

3) Create a periodical event in your system - LINUX
   * Access in a terminal "crontab -e" in order to change task schedules
   * Write "MIN HOUR * * * *  python3 path_to_file"




