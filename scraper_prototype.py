
# %%
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
        website_url (str): The URL of the product type to be scraped.  
    
    """

    def __init__(self, website_url:str):
        """
        See help(Scraper)
        """
        self.website_url = website_url
        self.driver = webdriver.Chrome()

    def navigate_to(self, url:str) -> webdriver.Chrome:
        """
        Navigates to a specific webpage. 

        Args: 
            url (str): The URL to be navigated to.
        
        """
        print("Navigating to: ", url)
        self.driver.get(url)


    def accept_cookies(self) -> webdriver.Chrome:
        """
        Accepts cookies for gear4music.com
        """
        print("Accepting cookies")
        self.navigate_to(self.website_url)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath(
            "//button[@id='banner-cookie-consent-allow-all']")
        accept_cookies_button.click()

    def retrieve_links_from_current_page(self):
        """
        Retrieves links from the driver's current page.
        """
        time.sleep(2)
        print("Retrieving links from current page")
        products = self.driver.find_elements_by_xpath(
            "//*[@class='g4m-grid-product-listing']/a")
        page_list_of_product_urls = [
            product.get_attribute("href") for product in products]
        #checks if final product has been reached
        if len(page_list_of_product_urls) < 40:
            return (page_list_of_product_urls, True)
        else:
            return (page_list_of_product_urls, False)

    def retrieve_product_links(self):
        """
        Retrieves all product links for this driver.
        """
        self.accept_cookies()
        list_of_product_urls = []
        i = 1
        while True:
            url = self.website_url + \
                "?page=" + str(i)
            self.navigate_to(url)
            (new_product_urls, end_of_pages) = self.retrieve_links_from_current_page()
            list_of_product_urls.extend(new_product_urls)
            if end_of_pages == True:
                break
            else: i += 1
        self.list_of_product_urls = list_of_product_urls
        return list_of_product_urls

    def collect_data_for_product(self, product_url:str):
        """
        Collects the data and image links for a given product.
        
        Args: 
            product_url(str): The url of the product to retrieve data from.
        """
        print("Collecting data from", product_url)
        time.sleep(1)
        self.navigate_to(product_url)
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
        #retrieve the images
        main_image = self.driver.find_element_by_xpath(
            "//img[@class='main-image']"
        ).get_attribute("src")
        other_images_container = self.driver.find_elements_by_xpath(
            "//li[@class='image']/a"
        )
        images = [image.get_attribute(
            "href") for image in other_images_container]
        images.insert(0,main_image)
        #checks if it's flagged as a sale
        special_messages = self.driver.find_elements_by_xpath(
            "//div[@class='info-row-special-msg info-row-item']"
        )
        sale = False
        for message in special_messages:
            if message.text == "SALE":
                sale = True
        #creates dictionary of the data
        data = {"product_uuid": str(product_uuid), 
                "product_ref": product_ref, 
                "product_name": product_name,
                "price": price, 
                "stock": stock,
                "description": description, 
                "images": images,
                "sale": sale }
        return data

    @staticmethod
    def create_directory(file_path):
        #TODO update this function so that the arguments are neater
        """
        Creates directory from current directory


        Args
            file_path: A tuple of the folders to the right directory.
        
        """
        current_directory = os.getcwd()
        target_directory = os.path.join(current_directory,*file_path)    
        print("Attempting to create", target_directory)
        Path(target_directory).mkdir(parents=True, exist_ok=True)
        return target_directory
    
    @staticmethod
    def save_data_to_file(data:dict):
        """
        Saves product data to correct location in directory. 

        Args:
            data(dict): A dictionary of data obtained by scraping the product pages. 
        """
        target_directory = Scraper.create_directory(("raw_data", data["product_ref"]))
        file_location = os.path.join(target_directory,"data.json")
        with open(file_location, "w") as f:
            json.dump(data, f)

    @staticmethod
    def download_image(file_location:str, image_url:str):
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
    def save_images_to_directory(data:dict):
        """
        Retrieves all the image files for data scraped from a product page. 

        Args:
            data(dict): The data scraped from a product page.
        """
        image_directory = Scraper.create_directory(("raw_data", data["product_ref"], "images"))
        i = 0
        for image in data["images"]:
            file_name = "".join(("image",str(i),".jpg"))
            file_location = os.path.join(image_directory,file_name)
            Scraper.download_image(file_location, image)
            i=+1
    

    def collect_data_and_store(self):
        """
        Collects and stores the data for a list of product urls obtained by the scraper. 
        """
        for url in self.list_of_product_urls:
            data = self.collect_data_for_product(url)
            Scraper.save_data_to_file(data)
            Scraper.save_images_to_directory(data)
            



# %%
if __name__ == "__main__":
    gear4music = Scraper("https://www.gear4music.com/podcasting/microphones")
    gear4music.retrieve_product_links()
    gear4music.collect_data_and_store()
# %%



# %%
