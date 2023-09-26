import pandas as pd
import tabula.io
from selenium import webdriver
import time
import os
import logging
import csv


logging.basicConfig(filename='Validate.log', level=logging.INFO)

"""
check if the file is existing if not it will generate the file "record.txt", else return true
"""
def FileGenerate():
    check_file = os.path.isfile('./record.txt')
    if not check_file:
        f = open("record.txt", "w")
        f.write("0")
    else:
        if os.stat("record.txt").st_size == 0:
            with open("record.txt", 'w') as f:
                f.write("0")
        else:
            return True

"""Dowload PDF"""
def Downloader(url):
    url_check = url+'?withshield=2'
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    options.add_experimental_option('prefs', {
    "plugins.plugins_list": [{"enabled": False,
                              "name": "Chrome PDF Viewer"}],
    "download.default_directory": os.getcwd(),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(options=options)
    driver.get(url_check)
    time.sleep(10)
    driver.get(url+'?withshield=3')
    time.sleep(5)
    driver.quit()

'''
Link Extractor
'''
def LinkExtract():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run Chrome in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.doe.gov.ph/retail-pump-prices-metro-manila')
    time.sleep(6)
    element = driver.find_element("xpath",
                                  '//*[@id="content-inner"]/div/div/div[2]/table/tbody/tr[1]/td[2]/span/span/a')
    link = element.get_attribute('href')
    return link


'''
Check Latest Update
'''
def WebsiteLastUpdate():
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run Chrome in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        driver.get('https://www.doe.gov.ph/retail-pump-prices-metro-manila')
        time.sleep(6)
        element = driver.find_element("xpath",'//*[@id="content-inner"]/div/div/div[2]/table/tbody/tr[1]/td[2]/span/span/a').text
        return element



'''Check Record last Update'''
def RecordedLastUpdate():
    # Check the last update of the program.
    with open("record.txt") as file:
        record = str(file.readline()).split(" ")[0:1]
        record = " ".join(map(str, record))
        return record

'''

'''
def LatestUpdate():
    RecordCurrent = RecordedLastUpdate()
    WebsiteCurrent = WebsiteLastUpdate()
    if RecordCurrent == WebsiteCurrent:
        return False
    else:
        with open("record.txt", "r") as f:
            contents = f.readlines()
        contents.insert(0, str(WebsiteCurrent) + ' \n')
        with open("record.txt", "w") as f:
            contents = "".join(contents)
            f.write(contents)
            f.close()
        return True


def ConvertPDFtoCSV():
    try:
        PDF = WebsiteLastUpdate()
        output = "updated.csv"
        tabula.io.convert_into(PDF, output, output_format="csv", pages="all", stream=True)
    except Exception as e:
        logging.exception("Error occurred in ConvertPDFtoCSV function.")


def DetailsExtract():
    try:
        #Extract Cities and details
        NCR = pd.read_csv('updated.csv', encoding='ISO-8859-1', usecols=[0]).dropna().values.tolist()
        Details = pd.read_csv('updated.csv', encoding='ISO-8859-1', usecols=[1,13]).fillna(0).values.tolist()
        Cities = []
        Product = []
        Price = []
        for city in NCR:
            if 'Cities' in str(city):
                None
            else:
                clean = str(city).replace("['", "").replace("']", "")
                Cities.append(clean)
        # Filter out other products from the pdf downloaded from the web
        for value in Details:
            if 'RON 95' in value or "RON 91" in value or "DIESEL" in value:
                string1, string2 = str(value).split(", ")
                Product.append(string1.replace("[", "").replace("'", ""))
                Price.append(string2.replace("]", "").replace("'", ""))

        # Compile the product and its price
        Details = list(zip(Product, Price))
        result = []
        # iterate over the list in steps of 3
        for i in range(0, len(Details), 3):
            Chunk = Details[i:i + 3]
            result.append(tuple(Chunk))

        # Combine the City and the prices of the product
        Combined = list(zip(Cities, result))
        logging.info('Script execution completed successfully.')
        # Compile the Cities and product prices in File
        df = pd.DataFrame(Combined, columns=['City', 'Products'])
        df = df.explode('Products')
        df[['Fuel', 'Price']] = pd.DataFrame(df['Products'].tolist(), index=df.index)
        df.drop('Products', axis=1, inplace=True)
        df = df.pivot(index='City', columns='Fuel', values='Price')
        df = df.reset_index()

        df.columns = ['City', 'DIESEL', 'RON 91', 'RON 95']

        try:
            # Update CSV base on the Dataframe made.
            data = [df.columns.tolist()] + df.values.tolist()

            ##CSV
            df.to_csv('my_data_by_column.csv', index=False)


        except Exception as e:
            logging.error(f'DataWrite(): Failed to update spreadsheet with error: {str(e)}')

    except Exception as e:
        logging.error(f'Error occurred: {str(e)}')






def Run():
    FileGenerate()
    if LatestUpdate():
        Downloader(LinkExtract())
        ConvertPDFtoCSV()
        DetailsExtract()
        delete_files()
    else:
        print("No New Update")


def delete_files():
    if os.path.exists(WebsiteLastUpdate()):
        # delete the file
        os.remove(WebsiteLastUpdate())
        os.remove("updated.csv")
    else:
        logging.warning(f"CurrentGasPrices.xlsx does not exist.")

Run()