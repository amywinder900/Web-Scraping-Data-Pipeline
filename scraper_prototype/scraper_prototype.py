
# %%
from gc import collect
import os
import json
from tokenize import String
import requests
import time
import uuid
import shutil
import boto3
import numpy as np
import pandas as pd
from psycopg2 import sql
from sklearn.exceptions import DataDimensionalityWarning
from sqlalchemy import create_engine, table
from datetime import datetime
from selenium import webdriver
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
# %%


class Scraper:
    """
    This class is used to scrape product data from gear4music.com

    Attributes:
        website_url (str): The URL of the Website to be scraped.

    """

    def __init__(self, website_url):
        """
        See help(Scraper)
        """
        self.website_url = website_url
        self.driver = webdriver.Chrome()
        self.raw_data_directory = 'raw_data'
        self.image_database_name = 'image'
        self.engine = create_engine(
            "postgresql+psycopg2://postgres:yhEfXmpY4Xyqzfz@productwebscraper.coiufgnqszer.us-east-1.rds.amazonaws.com:5432/postgres")
        self.engine.execute('''  CREATE TABLE if not exists raw_data(
                                    product_uuid TEXT, 
                                    product_ref TEXT,
                                    product_name TEXT,
                                    price TEXT,
                                    stock TEXT,
                                    description TEXT,
                                    images TEXT,
                                    sale TEXT);
						        CREATE TABLE if not exists images(
						            image_location TEXT,
					            	product_uuid TEXT);''')

    def accept_cookies(self,) -> None:
        """
        A method which loads the website and accepts cookies for a given xpath. 
        """
        print("Accepting cookies")
        self.driver.get(self.website_url)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath("//button[@id='banner-cookie-consent-allow-all']")
        accept_cookies_button.click()
        return None

    def retrieve_product_links(self, product_url: str, page: int) -> list:
        """
        Retrieves the product links for the section of the website specified. 

        Arguments: 
            product_url(str): The URL for the section of the website to be scraped. 
            page(int): The page number to scrape data from. 

        Returns:
            list_of_product_urls(list): The list of urls for products of this type.
        """
        print("Retriving links from page", page)
        url = product_url + \
            "?page=" + str(page)
        self.driver.get(url)
        time.sleep(3)
        products = self.driver.find_elements_by_xpath(
            "//*[@class='g4m-grid-product-listing']/a")
        list_of_product_urls = [product.get_attribute(
            "href") for product in products]
        return list_of_product_urls

    def check_stock(self) -> str:
        """
        This method checks the stock of a product. 

        Returns:
            stock(str): The stock number of the product on the webdriver's current page.
        """
        stock_container = self.driver.find_elements_by_xpath(
            "//div[@class='tooltip-container info-row-stock info-row-item']/div")[0]
        if stock_container.get_attribute("class") == "tooltip-source info-row-stock-msg instock in-stock":
            stock = stock_container.text.split()[0]
        else:
            stock = stock_container.text
        return stock

    def check_sale(self) -> bool:
        """
        This method checks whether a product is on sale. 

        Returns:
            sale(bool): True if the product on the webdriver's current page is on sale.
        """
        special_messages = self.driver.find_elements_by_xpath(
            "//div[@class='info-row-special-msg info-row-item']"
        )
        sale = False
        for message in special_messages:
            if message.text == "SALE":
                sale = True

        return sale

    def collect_image_links(self) -> list:
        """
        This method retrieves the links for the images of a product. 

        Returns:
            images(list): The links to the images of the product on the webdriver's current page.
        """
        main_image = self.driver.find_element_by_xpath(
            "//img[@class='main-image']"
        ).get_attribute("src")
        other_images_container = self.driver.find_elements_by_xpath(
            "//li[@class='image']/a"
        )
        images = [image.get_attribute(
            "href") for image in other_images_container]
        images.insert(0, main_image)

        return images

    def collect_product_data(self, product_url: str) -> dict:
        """
        Collects the data and image links for a given product.

        Args: 
            product_url(str): The url of the product to retrieve data from.

        Returns: 
            data(dict): The dictionary of data for the product.
        """
        self.driver.get(product_url)
        time.sleep(1)
        data = {"product_uuid": str(uuid.uuid4()),
                "product_ref": self.driver.find_element_by_xpath("//p[@class='prd-ref']").text.split(":")[1].strip(),
                "product_name": self.driver.find_element_by_xpath("//h1[@itemprop='name']").text,
                "price": self.driver.find_element_by_xpath("//span[@class='c-val']").text,
                "stock": self.check_stock(),
                "description": self.driver.find_element_by_xpath("//div[@class='slide']").text,
                "images": self.collect_image_links(),
                "sale": self.check_sale()
                }

        return data

    def __create_directories(self, product_ref: str):
        """
        Creates directories required to scrape data for a product.

        Args:
            product_ref(str): The reference number of the product.

        Returns:
            product_directory(str): The path to the directory for the product. 
            image_director (str): The path to the directory for images related to the product.

        """
        current_directory = os.getcwd()
        data_directory = os.path.join(
            current_directory, self.raw_data_directory)
        product_directory = os.path.join(data_directory, product_ref)
        image_directory = os.path.join(product_directory, "images")
        Path(data_directory).mkdir(parents=True, exist_ok=True)
        Path(image_directory).mkdir(parents=True, exist_ok=True)

        return (product_directory, image_directory)

    @staticmethod
    def __save_data_to_file(data: dict, product_directory: str):
        """
        Saves product data to correct location in directory. 

        Args:
            data(dict): A dictionary of data obtained by scraping the product pages. 
        """
        file_location = os.path.join(product_directory, "data.json")
        with open(file_location, "w") as f:
            json.dump(data, f)
        return None

    @staticmethod
    def __download_image(file_location: str, image_url: str):
        """
        Saves image file to correct directory.

        Args: 
            file_location(str): Location to save image in the directory.
            image_url(str): Location of the image.  
        """
        image_data = requests.get(image_url).content
        with open(file_location, "wb") as f:
            f.write(image_data)

        return None

    @staticmethod
    def __save_images_to_directory(data: dict, image_directory: str) -> dict:
        """
        Retrieves all the image files for data scraped from a product page. 

        Args:
            data(dict): The data scraped from a product page.

        Returns:
            image_database_dictionary(dict): A dictionary of data about the file locations. 
        """
        i = 0
        file_locations = []
        for image_src in data["images"]:
            file_name = "".join(("image", str(i), ".jpg"))
            local_file_location = os.path.join(image_directory, file_name)
            file_locations.append(local_file_location)
            Scraper.__download_image(local_file_location, image_src)
            i = +1

        # creates a dictionary of data about file locations
        image_database_dictionary = {
            "image_location": file_locations,
            "product_uuid": [data["product_uuid"]]*len(file_locations)
        }

        return image_database_dictionary

    def __upload_to_rds(self, data: dict, table_name: str):
        """
        Uploads the data to an instance of Amazon relational database. 

        Arguments: 
            data(dict): The dictionary of data to be uploaded to the Amazon RDS. 
            table_name(str): The name of the table to upload to. 
        """

        data_frame = pd.DataFrame(data)
        data_frame.to_sql(table_name, self.engine,
                          if_exists='append', index=False)
        return None

    def __check_if_exists_on_database(self, product_ref: str) -> bool:
        """
        Checks if the product has already been entered on the database. 

        Returns:
            downloaded(bool): The method will return True if the product reference matches one already in the database.
        """
        sql_query = """select product_ref from raw_data where product_ref = %(product_ref)s """
        table = pd.read_sql_query(sql_query, self.engine, params={
                                  "product_ref": product_ref})
        downloaded = True
        if table.empty:
            downloaded = False
        return downloaded

    def collect_product_data_and_store(self, url: str):
        """
        Collects the data for a product and stores it locally. 

        Arguments:
            url(str): The url for the product.

        Returns: 
            data(dict): The product data. Will return None if the product has already been scraped. 
            image_database_dictionary(dict): A dictionary containing file locations and the associated product uuid. 
        """
        print("Collecting data for ", url)
        data = self.collect_product_data(url)

        # checks if the product already exists in the database
        if self.__check_if_exists_on_database(data["product_ref"]):
            print("Already downloaded, skipping.")
            return None, None

        print("Creating directories")
        (product_directory, image_directory) = self.__create_directories(
            data["product_ref"])

        print("Saving to local machine.")
        Scraper.__save_data_to_file(data, product_directory)
        image_database_dictionary = Scraper.__save_images_to_directory(
            data, image_directory)

        return data, image_database_dictionary

    def collect_all_data_and_store(self, list_of_product_urls: list):
        """
        Collects and stores the data for a list of product urls obtained by the scraper. 
        """
        print("Collecting data from URLs.")
        i = 1
        # initalise lists for raw data database
        list_of_product_uuid = []
        list_of_product_ref = []
        list_of_product_name = []
        list_of_price = []
        list_of_stock = []
        list_of_description = []
        list_of_images = []
        list_of_sale = []
        # initalise lists for image database
        list_of_image_locations = []
        list_of_product_uuid_for_image_database = []

        # collects the data from the list of urls
        for url in list_of_product_urls:
            print("Product number", i)
            i += 1
            data, image_database_dictionary = self.collect_product_data_and_store(
                url)

            if data == None:
                continue
            else:
                try:
                    list_of_product_uuid.append(data["product_uuid"])
                    list_of_product_ref.append(data["product_ref"])
                    list_of_product_name.append(data["product_name"])
                    list_of_price.append(data["price"])
                    list_of_stock.append(data["stock"])
                    list_of_description.append(data["description"])
                    list_of_images.append(data["images"])
                    list_of_sale.append(data["sale"])

                    list_of_image_locations.extend(
                        image_database_dictionary["image_location"])
                    list_of_product_uuid_for_image_database.extend(
                        image_database_dictionary["product_uuid"])

                except NoSuchElementException:
                    print("Data collection failed for this URL, skipping.")

        # add data to dictionaries
        dictionary_of_data = {"product_uuid": list_of_product_uuid,
                              "product_ref": list_of_product_ref,
                              "product_name": list_of_product_name,
                              "price": list_of_price,
                              "stock": list_of_stock,
                              "description": list_of_description,
                              "images": list_of_images,
                              "sale": list_of_sale
                              }
        dictionary_of_image_data = {"image_location": list_of_image_locations,
                                    "product_uuid": list_of_product_uuid_for_image_database
                                    }

        print("Uploading to RDS")
        self.__upload_to_rds(dictionary_of_data, self.raw_data_directory)
        self.__upload_to_rds(dictionary_of_image_data,
                             self.image_database_name)
        return None

    def __delete_from_local_machine(self):
        """
        Removes the raw data from the local machine. 
        """
        directory = os.path.join(os.getcwd(), self.raw_data_directory)
        print("Deleting", directory)
        try:
            shutil.rmtree(directory)
        except FileNotFoundError:
            print("Can't find directory to delete.")
        return None

    def upload_to_bucket(self, bucket: str, delete_from_local: bool = True) -> None:
        """
        Uploads the data to a bucket. 

        Arguments:
            bucket(str): The bucket to upload to. 
            delete_from_local(bool): If true then the method will delete the raw data file from the local machine. True by default.
        """
        s3_client = boto3.client('s3')
        print("Uploading data to s3 bucket ", bucket,
              " is currently disabled to preserve resources.")
        # FIXME uncomment this method before deploying
        # data_directory = os.path.join(os.getcwd(), self.raw_data_directory)
        # print("Uploading ", data_directory, " to s3 bucket ", bucket)
        # i = 0
        # for subdirectories, directories, files in os.walk(data_directory):
        #     i += 1
        #     print("Uploading file number", i)
        #     for file in files:
        #         full_path = os.path.join(subdirectories, file)
        #         s3_client.upload_file(full_path, bucket, full_path)
        if delete_from_local == True:
            self.__delete_from_local_machine()
        return None

    def __check_total_number_of_pages(self, pages: int, product_url: str) -> int:
        """
        Checks how many pages are avaliable to scrape for the product. 

        Arguments:
            pages(int): The number of pages to be checked by the scraper
            product_url(str): The url of the product to be scraped. 

        Returns: 
            pages(int): The number of pages to be checked by the scraper, which is less than or equal to the total number of pages avaliable. 
        """

        self.driver.get(product_url)
        number_of_products = self.driver.find_elements_by_xpath(
            "//p[@data-test='plp-product-listing-count-message']/span")
        pages_avaliable = int(
            np.ceil(int(number_of_products[1].text)/int(number_of_products[0].text)))
        if pages_avaliable < pages:
            pages = pages_avaliable
            print("There are ", pages, " pages avalible to scrape.")
        return pages

    def run_scraper(self, pages: int, product_url: str) -> None:
        """
        Method to run the webscraper over a a given number of pages for a product.

        Arguments:
            pages(int): The number of pages to run the scraper over. 
            product_url(str): The url of the product to scrape. 
        """
        pages = self.__check_total_number_of_pages(pages, product_url)

        for i in range(1, pages+1):
            list_of_product_urls = self.retrieve_product_links(
                product_url, i)
            self.collect_all_data_and_store(list_of_product_urls)
        return None

    def close_scraper(self):
        """
        Closes the windows associated with the scraper. 
        """
        self.driver.quit()
        print("Quiting driver.")

        return None


# %%
if __name__ == "__main__":
    gear4music = Scraper("https://www.gear4music.com")
    gear4music.accept_cookies()
    gear4music.run_scraper(
        1,
        "https://www.gear4music.com/Microphones/Types.html")
    gear4music.close_scraper()
    gear4music.upload_to_bucket('productwebscraper')

# %%
