import unittest
from selenium.webdriver.support.ui import WebDriverWait
import unittest
from unittest.mock import MagicMock
from ib_insync import Execution
from projectIBKR import *
from investingAuto import *

class TestPortfolioApp(unittest.TestCase):

    def setUp(self):
        self.app = PortfolioApp()
        self.contract = MagicMock()
        self.contract.symbol = "AAPL"
        self.contract.conId = 265598
        self.contract.secType = "STK"
        self.contract.exchange = "NASDAQ"
        self.contract.currency = "USD"

    def test_updatePortfolio(self):
        self.app.updatePortfolio(self.contract, 100, 150, 15000, 140, 500, 0, "Account1")
        self.assertEqual(len(self.app.df), 1)
        self.assertEqual(self.app.df["Symbol"].iloc[0], "AAPL")
        self.assertEqual(self.app.df["Quantity"].iloc[0], 100)
        self.assertEqual(self.app.df["AverageCost"].iloc[0], 140)

    def test_nextValidId(self):
        self.app.start = MagicMock()
        self.app.nextValidId(5678)
        self.assertTrue(self.app.start.called)



class TestTransactionsApp(unittest.TestCase):
    def setUp(self):
        self.app = TransactionsApp()

    def test_execDetails(self):
        reqId = 1
        contract = Contract()
        contract.symbol = 'AAPL'
        contract.conId = 265598
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        execution = Execution()
        execution.execId = '123'
        execution.side = 'BUY'
        execution.shares = 10
        execution.price = 150.0
        execution.time = '2023-08-08 10:00:00'

        self.app.execDetails(reqId, contract, execution)

        self.assertEqual(self.app.id, ['123'])
        self.assertEqual(self.app.symbol, ['AAPL'])
        self.assertEqual(self.app.isin, ['US0378331005'])
        self.assertEqual(self.app.sectype, ['STK'])
        self.assertEqual(self.app.exchange, ['SMART'])
        self.assertEqual(self.app.currency, ['USD'])
        self.assertEqual(self.app.action, ['BUY'])
        self.assertEqual(self.app.quantity, [10])
        self.assertEqual(self.app.executionPrice, [150.0])
        self.assertEqual(self.app.executionTime, ['2023-08-08 10:00:00'])

    def test_nextValidId(self):
        self.app.start = MagicMock()
        self.app.nextValidId(5678)
        self.assertTrue(self.app.start.called)

    def test_accountDownloadEnd(self):
        accountName = 'TestAccount'

        self.app.accountDownloadEnd(accountName)

        self.assertTrue(True)  




class TestGeneralIBKR(unittest.TestCase):
    def test_get_isin(self):
        result = get_isin(265598)
        time.sleep(1)
        self.assertEqual(result, 'US0378331005')

    def test_generate_portfolio(self):
        generate_portfolio()

        for file in glob.glob("Datos/porfolio.csv"):
            self.assertTrue(file)

    def test_generate_transactions(self):
        generate_transactions()

        for file in glob.glob("Datos/Transactions*.csv"):
            self.assertTrue(file)





class TestInvesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        time.sleep(25)
        driver = get_driver()
        cls.driver = driver
        
        #driver.maximize_window()
        driver.get("https://www.investing.com/")
        time.sleep(5)

        #Cookies accept
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()

        #Popup appears
        try:
            driver.find_element(By.CLASS_NAME, 'popupCloseIcon.largeBannerCloser').click()
        except ElementNotInteractableException:
            pass

            
        #Log In Screen
        driver.find_element(By.XPATH, '//*[@id="userAccount"]/div/a[1]').click()

        #Account data
        with open("userCredentials.txt", 'r') as file:
            for line in file:
                if 'userInvesting' in line:
                    userInvesting = line.strip().split('=')[1].strip()
                elif 'passInvesting' in line:
                    passInvesting = line.strip().split('=')[1].strip()

        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginFormUser_email"]'))).send_keys(userInvesting)
        driver.find_element(By.XPATH, '//*[@id="loginForm_password"]').send_keys(passInvesting)

        #Log in button
        driver.find_element(By.XPATH, '//*[@id="signup"]/a').click()
        time.sleep(6)
        #My portfolio button
        #WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="navMenu"]/ul/li[2]/a'))).click()
        driver.get("https://www.investing.com/portfolio")
        time.sleep(5)

        
        #Prepare new transactions
        data = {
            "Id": [10, 12],
            "Symbol": ["AAPL", "TSLA"],
            "ISIN": ["US0378331005", "US88160R1014"],
            "Action": ["BUY", "SELL"],
            "Quantity": [100, 140],
            "Price": [30, 30],
            "Time": ["2023-08-09 19:23:23", "2023-08-09 19:23:23"]
            }
        transactions = pd.DataFrame(data)
        try:
            for file in glob.glob("Datos/Transactions*.csv"):
                os.remove(file)
        except FileNotFoundError:
            pass

        #Save
        now = datetime.now().strftime('%Y%m%d %H%M%S')
        transactions.to_csv('Datos/Transactions' + now + '.csv', index = False)

    
    @classmethod
    def tearDownClass(cls):
        print("Test finished")

    def test_a_create_porfolio(self):
        create_portfolio("PRUEBA")
        create_portfolio("TEST")
        self.assertTrue("PRUEBA" in driver.page_source)
        self.assertTrue("TEST" in driver.page_source)

    def test_b_change_portfolio_tab(self):
        change_portfolio_tab("PRUEBA")
        selected_tab = driver.find_element(By.CSS_SELECTOR, '.portfolioTab.selected')
        self.assertEqual(selected_tab.get_attribute('title'), 'PRUEBA')

    def test_c_delete_portfolio(self):
        delete_portfolio('TEST')
        time.sleep(2)
        selected_tab = driver.find_element(By.CSS_SELECTOR, '.portfolioTab.selected')
        self.assertNotEqual(selected_tab.get_attribute('title'), 'TEST')

    def test_d_add_position(self):
        date = datetime.today()
        date = date.strftime("%m/%d/%Y")
        add_position(23,"AAPL", "US0378331005", "BUY", 10, 20, date)
        self.assertTrue("AAPL" in driver.page_source)

        add_position(12,"TSLA", "US88160R1014", "SELL", 10, 20, date)
        add_position(12,"TSLA", "US88160R1014", "SELL", 10, 20, date)
        self.assertTrue("TSLA" in driver.page_source)

    def test_e_get_position_quantity(self):
        value = get_position_quantity("AAPL")
        self.assertEqual(value, 10)

        value = get_position_quantity("AAPL", "BUY")
        self.assertEqual(value, 10)
        
        value = get_position_quantity("NonExistentPosition")
        self.assertEqual(value, 0)
    
    def test_f_get_transactions(self):
        df = get_transactions()
        self.assertIsInstance(df, type(pd.DataFrame()))
    

    def test_g_close_position(self):
        date = datetime.today()
        date = date.strftime("%m/%d/%Y")
        manage_container_father("AAPL", "EXPAND")
        close_position(10, 5, date)
        
        quantity = get_position_quantity("AAPL")
        self.assertEqual(quantity, 0)

    def test_h_close_transaction(self):
        date = datetime.today()
        date = date.strftime("%m/%d/%Y")
        close_transaction(12, "TSLA", "US88160R1014", "SELL", 20, 20, date)

        type = "SELL"
        if (type == "SELL"): 
            quantity = get_position_quantity("TSLA")
        self.assertEqual(quantity, 0)

    def test_i_process_portfolio(self):
        delete_portfolio("PRUEBA")
        create_portfolio("Cartera1")


        data = {
            "Id": [10],
            "Symbol": ["AAPL"],
            "ISIN": ["US0378331005"],
            "Action": ["BOT"],
            "Quantity": [10],
            "Price": [150.0],
            "Time": [datetime.now()]
        }
        transactions = pd.DataFrame(data)
        
        process_portfolio("Cartera1", transactions)
        
        quantity = get_position_quantity("AAPL")

        self.assertEqual(quantity, 10)

        delete_portfolio("Cartera1")

    def test_j_portfolio_initiation(self):
        
        data = {
                "Symbol": ["AAPL", "AMZN", "BBVA", "FORD"],
                "ISIN": ["US0378331005", "US0231351067", "US05946K1016", "US3498623004"],
                "SecType": ["STK", "STK", "STK", "STK"],
                "Currency": ["USD", "USD", "USD", "USD"],
                "Quantity": [50.0, 53.0, 40.0, 15.0],
                "AverageCost": [190.1228, 129.8548148, 7.707275, 0.93076]
                }      

        portfolio = pd.DataFrame(data)

        try:
            for file in glob.glob("Datos/portfolio.csv"):
                os.remove(file)
        except FileNotFoundError:
            pass

        #Save
        portfolio.to_csv('Datos/portfolio.csv', index = False)

        portfolio_initiation()

        change_portfolio_tab("Cartera1")

        investing_cartera = pd.read_html(driver.page_source)[0]
        investing_cartera.set_index(investing_cartera.iloc[:,2], inplace=True)
        investing_cartera = investing_cartera.iloc[:, 4:6]

        self.assertFalse(investing_cartera.empty)

        delete_portfolio("Cartera1")
        delete_portfolio("Cartera2-Largo")
        delete_portfolio("Cartera3-Corto")



    def test_k_integration(self):


        data_portfolio = [
        ['AAPL', 'US0378331005', 'STK', 'USD', 10.0, 190.1228],
        ['LYFT', 'US55087P1049', 'STK', 'USD', 40.0, 187.22]
        ]
        data_transactions = [
                [1, 'AAPL', 'US0378331005', 'BOT', 15, 10, '2023-08-09 19:23:23'],
                [2, 'TSLA', 'US88160R1014', 'SLD', 40, 10, '2023-08-09 19:23:23'],
                [3, 'AAPL', 'US0378331005', 'BOT', 15, 10, '2023-08-09 19:23:23'],
                [4, 'AAPL', 'US0378331005', 'SLD', 40, 10, '2023-08-09 19:23:23'],
                [5, 'GOOGL', 'US02079K3059', 'BOT', 50, 10, '2023-08-09 19:23:23'],
                [6, 'TSLA', 'US88160R1014', 'SLD', 40, 10, '2023-08-09 19:23:23'],
                [7, 'AAPL', 'US0378331005', 'SLD', 30, 10, '2023-08-09 19:23:23'],
                [8, 'GOOGL', 'US02079K3059', 'BOT', 50, 10, '2023-08-09 19:23:23'],
                [9, 'AAPL', 'US0378331005', 'BOT', 30, 10, '2023-08-09 19:23:23'],
                [10, 'AAPL', 'US0378331005', 'SLD', 10, 30, '2023-08-09 19:23:23'],
                [11, 'GOOGL', 'US02079K3059', 'SLD', 20, 10, '2023-08-09 19:23:23'],
                [12, 'AAPL', 'US0378331005', 'BOT', 5, 30, '2023-08-09 19:23:23'],
                [13, 'AAPL', 'US0378331005', 'BOT', 20, 30, '2023-08-09 19:23:23'],
                [14, 'AAPL', 'US0378331005', 'SLD', 50, 30, '2023-08-09 19:23:23'],
                [15, 'AAPL', 'US0378331005', 'BOT', 80, 30, '2023-08-09 19:23:23'],
                [16, 'TSLA', 'US88160R1014', 'BOT', 10, 10, '2023-08-09 19:23:23'],
                [17, 'AAPL', 'US0378331005', 'SLD', 20, 30, '2023-08-09 19:23:23']
                ]   
        
        columns_portfolio = ['Symbol', 'ISIN', 'SecType', 'Currency', 'Quantity', 'AverageCost']
        columns_transactions = ['Id', 'Symbol', 'ISIN', 'Action', 'Quantity', 'Price', 'Time']
        
        portfolio = pd.DataFrame(data_portfolio, columns=columns_portfolio)
        transactions = pd.DataFrame(data_transactions, columns=columns_transactions)
        
        try:
            for file in glob.glob("Datos/portfolio.csv"):
                os.remove(file)
        except FileNotFoundError:
            pass
        try:
            for file in glob.glob("Datos/Transactions*.csv"):
                os.remove(file)
        except FileNotFoundError:
            pass

        #Save
        now = datetime.now().strftime('%Y%m%d %H%M%S')
        transactions.to_csv('Datos/Transactions' + now + '.csv', index = False)
        portfolio.to_csv('Datos/portfolio.csv', index = False)

        self.driver.delete_all_cookies()
        self.driver.refresh()

        main_investing()

        self.driver.delete_all_cookies()
        self.driver.refresh()
        

        main_investing()

        change_portfolio_tab("Cartera1")
        self.assertEqual(get_position_quantity("AAPL", "BUY"), 25)
        self.assertEqual(get_position_quantity("TSLA", "SELL"), 70)
        self.assertEqual(get_position_quantity("GOOGL", "BUY"), 80)

        change_portfolio_tab("Cartera2-Largo")
        self.assertEqual(get_position_quantity("AAPL", "BUY"), 20)
        self.assertEqual(get_position_quantity("TSLA", "BUY"), 0)
        self.assertEqual(get_position_quantity("GOOGL", "BUY"), 20)

        change_portfolio_tab("Cartera3-Corto")
        self.assertEqual(get_position_quantity("AAPL", "BUY"), 0)
        self.assertEqual(get_position_quantity("TSLA", "BUY"), 70)
        self.assertEqual(get_position_quantity("GOOGL", "BUY"), 0)

        self.driver.close()

        




        



if __name__ == '__main__':
    unittest.main()