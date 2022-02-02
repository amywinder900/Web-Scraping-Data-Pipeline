
# %%
from email.mime import image
import os
import json
import requests
import time
import uuid
from selenium import webdriver
from pathlib import Path
# %%


class Scraper:
    """
    This class is used to scrape product data from gear4music.com

    Attributes: 
        webpage_url (str): The URL of the product type to be scraped.  

    """

    def __init__(self, webpage_url: str):
        """
        See help(Scraper)
        """
        self.webpage_url = webpage_url
        self.driver = webdriver.Chrome()

    def __accept_cookies(self) -> webdriver.Chrome:
        """
        A private method which accepts cookies for gear4music.com
        """
        print("Accepting cookies")
        self.driver.get(self.webpage_url)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath(
            "//button[@id='banner-cookie-consent-allow-all']")
        accept_cookies_button.click()

    def __retrieve_links_from_current_page(self):
        """
        A private method which retrieves links from the driver's current page.
        """
        time.sleep(2)
        products = self.driver.find_elements_by_xpath(
            "//*[@class='g4m-grid-product-listing']/a")
        page_list_of_product_urls = [
            product.get_attribute("href") for product in products]
        return (page_list_of_product_urls)

    def retrieve_product_links(self):
        """
        Retrieves all product links for this driver.
        """
        self.__accept_cookies()
        list_of_product_urls = []
        i = 1
        unique_urls_collected = 0
        while True:
            print("Retriving links from page", i)
            url = self.webpage_url + \
                "?page=" + str(i)
            self.driver.get(url)
            new_product_urls = self.__retrieve_links_from_current_page()
            list_of_product_urls.extend(new_product_urls)
            #removes duplicates
            list_of_product_urls = [i for n, i in enumerate(list_of_product_urls)if i not in list_of_product_urls[:n]]
            #checks if any new urls have been collected
            new_total_urls_collected = len(list_of_product_urls)
            if new_total_urls_collected == unique_urls_collected:
                break
            else:
                i += 1
                unique_urls_collected = new_total_urls_collected

        self.list_of_product_urls = list_of_product_urls
        return list_of_product_urls

    def collect_data_for_product(self, product_url: str):
        """
        Collects the data and image links for a given product.

        Args: 
            product_url(str): The url of the product to retrieve data from.
        """
        print("Collecting data from", product_url)
        time.sleep(1)
        self.driver.get(product_url)
        product_ref = self.driver.find_element_by_xpath(
            "//p[@class='prd-ref']").text.split(":")[1].strip()
        product_uuid = uuid.uuid4()
        product_name = self.driver.find_element_by_xpath(
            "//h1[@itemprop='name']").text
        price = self.driver.find_element_by_xpath(
            "//span[@class='c-val']").text
        stock = self.driver.find_element_by_xpath(
            "//div[@class='tooltip-source info-row-stock-msg instock in-stock']").text.split()[0]
        description = self.driver.find_element_by_xpath(
            "//div[@class='slide']").text.split(":", 1)[1]
        # retrieve the images
        main_image = self.driver.find_element_by_xpath(
            "//img[@class='main-image']"
        ).get_attribute("src")
        other_images_container = self.driver.find_elements_by_xpath(
            "//li[@class='image']/a"
        )
        images = [image.get_attribute(
            "href") for image in other_images_container]
        images.insert(0, main_image)
        # checks if it's flagged as a sale
        special_messages = self.driver.find_elements_by_xpath(
            "//div[@class='info-row-special-msg info-row-item']"
        )
        sale = False
        for message in special_messages:
            if message.text == "SALE":
                sale = True
        # creates dictionary of the data
        data = {"product_uuid": str(product_uuid),
                "product_ref": product_ref,
                "product_name": product_name,
                "price": price,
                "stock": stock,
                "description": description,
                "images": images,
                "sale": sale}
        return data

    @staticmethod
    def __create_directories(product_ref:str):
        # TODO update this function so that the arguments are neater
        """
        Creates directories required to scrape data for a product.


        Args
            product_ref(str): The reference number of the product.

        """
        current_directory = os.getcwd()
        data_directory = os.path.join(current_directory, "raw_data")
        product_directory = os.path.join(data_directory, product_ref)
        image_directory = os.path.join(product_directory, "images")
        Path(data_directory).mkdir(parents=True, exist_ok=True)
        Path(image_directory).mkdir(parents=True, exist_ok=True)
        return (product_directory, image_directory)

    @staticmethod
    def save_data_to_file(data: dict, product_directory: str):
        """
        Saves product data to correct location in directory. 

        Args:
            data(dict): A dictionary of data obtained by scraping the product pages. 
        """
        file_location = os.path.join(product_directory, "data.json")
        with open(file_location, "w") as f:
            json.dump(data, f)

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

    @staticmethod
    def save_images_to_directory(data: dict, image_directory):
        """
        Retrieves all the image files for data scraped from a product page. 

        Args:
            data(dict): The data scraped from a product page.
        """
        i = 0
        for image_src in data["images"]:
            file_name = "".join(("image", str(i), ".jpg"))
            local_file_location = os.path.join(image_directory, file_name)
            Scraper.__download_image(local_file_location, image_src)
            i = +1

    def collect_data_and_store(self):
        """
        Collects and stores the data for a list of product urls obtained by the scraper. 
        """
        print("Collecting data from URLs.")
        print(type(self.list_of_product_urls))
        for url in self.list_of_product_urls:
            data = self.collect_data_for_product(url)
            (product_directory, image_directory) = Scraper.__create_directories(
                data["product_ref"])
            Scraper.save_data_to_file(data, product_directory)
            Scraper.save_images_to_directory(data, image_directory)


# %%
if __name__ == "__main__":
    gear4music = Scraper("https://www.gear4music.com/dj-equipment/mobile-dj/microphones?_gl=1*1wxixgz*_ga*MjE1MDU3NzY1LjE2NDM4MTQ0NzE.*_up*MQ..")
    gear4music.retrieve_product_links()
    gear4music.collect_data_and_store()
# %%
# %%
