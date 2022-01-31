
# %%
from email.mime import image
from gc import collect
from selenium import webdriver
import time
import uuid
from pathlib import Path
import os
import json
# %%


class scraper():
    def __init__(self, URL):
        self.URL = URL
        self.driver = webdriver.Chrome()

    def navigate_to(self, URL) -> webdriver.Chrome:
        self.driver.get(URL)
        time.sleep(1)

    def accept_cookies(self) -> webdriver.Chrome:
        print("Accepting cookies")
        self.navigate_to(self.URL)
        time.sleep(2)
        accept_cookies_button = self.driver.find_element_by_xpath(
            "//button[@id='banner-cookie-consent-allow-all']")
        accept_cookies_button.click()

    def retrieve_links_from_current_page(self):
        time.sleep(2)
        print("Retrieving links")
        products = self.driver.find_elements_by_xpath(
            "//*[@class='g4m-grid-product-listing']/a")
        page_list_of_product_urls = [
            product.get_attribute("href") for product in products]
        return page_list_of_product_urls

    def retrieve_links(self, number_of_pages=2):
        self.accept_cookies()
        print("Retrieving links.")
        list_of_product_urls = []
        for i in range(number_of_pages):
            url = self.URL + \
                "?page=" + str(i+1)
            self.navigate_to(url)
            list_of_product_urls.extend(
                self.retrieve_links_from_current_page())
        print(list_of_product_urls)
        self.list_of_product_urls = list_of_product_urls
        return list_of_product_urls

    def collect_data_from_url(self, url):
        print("Collecting data from", url)
        time.sleep(1)
        self.navigate_to(url)
        product_ref = self.driver.find_element_by_xpath(
            "//p[@class='prd-ref']").text.split(":")[1].strip()
        product_uuid = uuid.uuid4()
        product_name = self.driver.find_element_by_xpath(
            "//h1[@itemprop='name']").text
        price = self.driver.find_element_by_xpath(
            "//span[@class='c-val']").text
        # TODO deal with case where out of stock
        stock = self.driver.find_element_by_xpath(
            "//div[@class='tooltip-source info-row-stock-msg instock in-stock']").text.split()[0]
        description = self.driver.find_element_by_xpath(
            "//div[@class='slide']").text.split(":", 1)[1]
        main_image = self.driver.find_element_by_xpath(
            "//img[@class='main-image']"
        ).get_attribute("src")
        other_images_container = self.driver.find_elements_by_xpath(
            "//li[@class='image']/a"
        )
        other_images = [image.get_attribute(
            "href") for image in other_images_container]
        # check if it's flagged as a sale
        special_messages = self.driver.find_elements_by_xpath(
            "//div[@class='info-row-special-msg info-row-item']"
        )
        sale = False
        for message in special_messages:
            if message.text == "SALE":
                sale = True

        data = {"product_uuid": str(product_uuid), 
                "product_ref": product_ref, 
                "product_name": product_name,
                "stock": stock,
                "description": description, 
                "main_image": main_image,
                "other_images":other_images,
                "sale": sale }
        return data

    @staticmethod
    def save_to_file(data):
        current_directory = os.getcwd()
        target_directory = os.path.join(current_directory,"raw_data", data["product_ref"])
        file_location = os.path.join(target_directory,"data.json")
        print("attempting to create", target_directory)
        Path(target_directory).mkdir(parents=True, exist_ok=True)
        with open(file_location, "w") as f:
            json.dump(data, f)

    def collect_data_and_store(self):
        for url in self.list_of_product_urls: 
            data = self.collect_data_from_url(url)
            self.save_to_file(data)
        #TODO deal with images


# %%
if __name__ == "__main__":
    gear4music = scraper("https://www.gear4music.com/podcasting/microphones")
    gear4music.retrieve_links(1)
    gear4music.collect_data_and_store()
# %%

# %%
