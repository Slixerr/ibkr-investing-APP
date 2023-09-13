import csv
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Timer
from ibapi.execution import ExecutionFilter
import pandas as pd
from datetime import datetime
import glob, os
import ib_insync as ibis
import re



class PortfolioApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.df = pd.DataFrame(columns=["Symbol", "ISIN", "SecType", "Currency", "Quantity", "AverageCost"])

    def nextValidId(self, orderId):
        self.start()

    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        isin = get_isin(int(contract.conId))
        data = {
            "Symbol": [contract.symbol],
            "ISIN": [isin],
            "SecType": [contract.secType],
            "Currency": [contract.currency],
            "Quantity": [position],
            "AverageCost": [averageCost]
        }

        new_df = pd.DataFrame(data)
        self.df = pd.concat([self.df, new_df], ignore_index=True)

    def accountDownloadEnd(self, accountName: str):
        print("AccountDownloadEnd. Account:", accountName)

    def start(self):
        self.reqAccountUpdates(True, "")

    def stop(self):
        self.df.to_csv("Datos/portfolio.csv", index=False)
        self.reqAccountUpdates(False, "")
        self.done = True
        self.disconnect()

class TransactionsApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)

        self.id = []
        self.symbol = []
        self.isin = []
        self.sectype = []
        self.exchange = []
        self.currency =[]
        self.action = []
        self.quantity = []
        self.executionPrice = []
        self.executionTime = []


    def nextValidId(self, orderId):
        self.start()

    def execDetails(self, reqId, contract, execution):
        self.id.append(execution.execId)
        self.symbol.append(contract.symbol)
        self.isin.append(get_isin(int(contract.conId)))
        self.sectype.append(contract.secType)
        self.exchange.append(contract.exchange)
        self.currency.append(contract.currency)
        self.action.append(execution.side)
        self.quantity.append(execution.shares)
        self.executionPrice.append(execution.price)
        self.executionTime.append(execution.time)

    def accountDownloadEnd(self, accountName: str): #
        print("AccountDownloadEnd. Account:", accountName)

    def start(self):
        self.reqExecutions(1, ExecutionFilter())

    def stop(self):
        self.done = True
        self.disconnect()


def get_isin(id):
    ib = ibis.IB()
    ib.connect('127.0.0.1', 7497, 1000)
    contract  = ibis.Contract(conId=id)
    ib.qualifyContracts(contract)
    details = ib.reqContractDetails(contract)
    isin_match = re.search(r"ISIN',\svalue='([^']+)'", str(details[0]))
    isin = isin_match.group(1)
    ib.disconnect()
    time.sleep(0.5)
    return isin
    

def generate_portfolio():
    app = PortfolioApp()
    app.connect("127.0.0.1", 7497, 0)
    Timer(10, app.stop).start()
    app.run()

def generate_transactions():
    app = TransactionsApp()
    app.connect("127.0.0.1", 7497, 1)
    Timer(10, app.stop).start()
    app.run()

    df = pd.DataFrame()
    for i in range(len(app.id)):
        new_row = pd.DataFrame({'Id': app.id[i], 'Symbol': app.symbol[i], 'ISIN': app.isin[i], 'Action': app.action[i], 'Quantity': app.quantity[i], 'Price': app.executionPrice[i], 'Time': app.executionTime[i]}, index=[0])
        df = pd.concat([df, new_row])

    try:
        
        df['Time'] =  pd.to_datetime(df['Time'], format='%Y%m%d  %H:%M:%S')
        
        df.sort_values(by=['Time'], inplace=True)
        
    except KeyError:
        columns = ['Id', 'Symbol', 'ISIN', 'Action', 'Quantity', 'Price', 'Time']
        df = pd.DataFrame(columns=columns)
        print("No transactions since last time")

    #Delete older Transactions entries before saving
    try:
        for file in glob.glob("Datos/Transactions*.csv"):
            file_time = datetime.strptime(file[18:-4], '%Y%m%d %H%M%S')
            os.remove(file)

        df = df.loc[df["Time"] >= file_time]
        
    except (KeyError, UnboundLocalError)  as e:
        pass

    #Save
    now = datetime.now().strftime('%Y%m%d %H%M%S')
    df.to_csv('Datos/Transactions' + now + '.csv', index = False)


