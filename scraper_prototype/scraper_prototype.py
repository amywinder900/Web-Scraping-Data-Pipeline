
# %%
from gc import collect
import os
import json
import requests
import time
import uuid
import shutil
import boto3
import pandas as pd
from sklearn.exceptions import DataDimensionalityWarning
from sqlalchemy import create_engine, table
from datetime import datetime
from selenium import webdriver
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement
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
        self.raw_data_directory = 'raw_data_' + datetime.today().strftime('%Y%m%d')
        self.image_database_name = 'image_' + datetime.today().strftime('%Y%m%d')

    def accept_cookies(self, xpath: str) -> None:
        """
        A method which loads the website and accepts cookies for a given xpath. 

        Arguments: 
            xpath(str): The xpath of the accept cookies
        """
        print("Accepting cookies")
        self.driver.get(self.website_url)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath(xpath)
        accept_cookies_button.click()
        return None

    def __retrieve_links_from_current_page(self, product_grid_xpath: str) -> list:
        """
        A private method which retrieves links from the driver's current page.

        Arguments:
            product_grid_xpath (str): The xpath for the container which holds the products.  


        Returns:
            page_list_of_product_urls(list): The list of the urls on the current page of the driver.
        """
        time.sleep(3)
        products = self.driver.find_elements_by_xpath(product_grid_xpath)
        page_list_of_product_urls = [
            product.get_attribute("href") for product in products]
        return page_list_of_product_urls

    def retrieve_product_links(self, product_url: str, product_grid_xpath: str, start_page) -> list:
        """
        #TODO update docstring

        Retrieves the product links for the section of the website specified. 

        Arguments: 
            product_url(str): The URL for the section of the website to be scraped. 
            product_grid_xpath(str): The xpath for the container which holds the products.  

        Returns:
            list_of_product_urls(list): The list of urls for products of this type.
        """
        list_of_product_urls = []
        unique_urls_collected = 0
        for page in range(start_page, start_page + 1):
            print("Retriving links from page", page)
            url = product_url + \
                "?page=" + str(page)
            self.driver.get(url)
            new_product_urls = self.__retrieve_links_from_current_page(
                product_grid_xpath)
            list_of_product_urls.extend(new_product_urls)
            # Removes duplicates from the list of urls
            list_of_product_urls = [i for n, i in enumerate(
                list_of_product_urls)if i not in list_of_product_urls[:n]]
            # Stops the loop if no new product urls have been collected
            new_total_urls_collected = len(list_of_product_urls)
            if new_total_urls_collected == unique_urls_collected:
                break
            else:
                unique_urls_collected = new_total_urls_collected

        self.list_of_product_urls = list_of_product_urls

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
    def __save_images_to_directory(data: dict, image_directory: str):
        """
        Retrieves all the image files for data scraped from a product page. 

        Args:
            data(dict): The data scraped from a product page.
        """
        i = 0
        file_locations = []
        for image_src in data["images"]:
            file_name = "".join(("image", str(i), ".jpg"))
            local_file_location = os.path.join(image_directory, file_name)
            file_locations.append(local_file_location)
            Scraper.__download_image(local_file_location, image_src)
            i = +1
        return file_locations

    def __upload_to_rds(self, data: dict, table_name: str):
        """
        Uploads the data to an instance of Amazon relational database. 

        Arguments: 
            data(dict): The dictionary of data to be uploaded to the Amazon RDS. 
            table_name(str): The name of the table to upload to. 
        """
        engine = create_engine(
            "postgresql+psycopg2://postgres:yhEfXmpY4Xyqzfz@productwebscraper.coiufgnqszer.us-east-1.rds.amazonaws.com:5432/postgres")
        data_frame = pd.DataFrame(data)
        data_frame.to_sql(table_name, engine,
                          if_exists='append', index=False)
        return None

    def __upload_image_data_to_rds(self, data: dict, image_directory: str):
        """
        Uploads information about the images to a Amazon relational database. 
        """
        i = 0
        for image in data["images"]:
            image_name = "image" + str(i) + ".jpg"
            image_data = {
                "image_uuid": str(uuid.uuid4()),
                "product_uuid": data["product_uuid"],
                "image_path": os.path.join(image_directory, image_name)
            }
            self.__upload_to_rds(image_data, self.image_database_name)
        return None

    def collect_product_data_and_store(self, url: str):
        """
        Collects the data for a product and stores it locally. 

        Arguments:
            url(str): The url for the product.
        """
        print("Collecting data for ", url)
        data = self.collect_product_data(url)
        print("Creating directories")
        (product_directory, image_directory) = self.__create_directories(
            data["product_ref"])
        print("Saving to local machine.")
        Scraper.__save_data_to_file(data, product_directory)
        image_file_locations = Scraper.__save_images_to_directory(
            data, image_directory)
        image_database_dictionary = {
            "image_location": image_file_locations,
            "product_uuid": [data["product_uuid"]]*len(image_file_locations)
        }
        return data, image_database_dictionary

    def collect_all_data_and_store(self):
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

        for url in self.list_of_product_urls:
            print("Product number", i)
            i += 1
            try:
                data, image_database_dictionary = self.collect_product_data_and_store(
                    url)
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
            except:
                print("Data collection failted for this URL, skipping.")

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
        self.__upload_to_rds(dictionary_of_image_data, self.image_database_name)
        return None

    def __delete_from_local_machine(self):
        """
        Removes the raw data from the local machine. 
        """
        directory = os.path.join(os.getcwd(), self.raw_data_directory)
        print("Deleting", directory)
        shutil.rmtree(directory)
        return None

    def upload_to_bucket(self, bucket: str, delete_from_local: bool = True) -> None:
        """
        Uploads the data to a bucket. 

        Arguments:
            bucket(str): The bucket to upload to. 
            delete_from_local(bool): If true then the method will delete the raw data file from the local machine. True by default.
        """
        s3_client = boto3.client('s3')
        print("Uploading data to s3 bucket ", bucket)
        data_directory = os.path.join(os.getcwd(), self.raw_data_directory)
        print("Uploading ", data_directory, " to s3 bucket ", bucket)
        i = 0
        for subdirectories, directories, files in os.walk(data_directory):
            i += 1
            print("Uploading file number", i)
            for file in files:
                full_path = os.path.join(subdirectories, file)
                s3_client.upload_file(full_path, bucket, full_path)
        if delete_from_local == True:
            self.__delete_from_local_machine()
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
    gear4music.accept_cookies(
        "//button[@id='banner-cookie-consent-allow-all']")
    gear4music.retrieve_product_links(
        "https://www.gear4music.com/Microphones/Types.html", "//*[@class='g4m-grid-product-listing']/a", 1)
    gear4music.collect_all_data_and_store()
    gear4music.close_scraper()
    gear4music.upload_to_bucket('productwebscraper')

# %%


data = {"hello": [1, 2, 3], "world": ["one", "two", "three"]}

engine = create_engine(
    "postgresql+psycopg2://postgres:yhEfXmpY4Xyqzfz@productwebscraper.coiufgnqszer.us-east-1.rds.amazonaws.com:5432/postgres")
data_frame = pd.DataFrame(data)
data_frame.to_sql("table1", engine,
                  if_exists='append', index=False)
# %%
