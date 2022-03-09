import sys
sys.path.append("../Web-Scraping-Data-Pipeline")
print(sys.path)
from scraper_prototype.scraper_prototype import Scraper
import unittest
import os
from selenium.common.exceptions import NoSuchElementException


class ScraperCollectURLSTestCase(unittest.TestCase):
    def setUp(self):
        self.scraper = Scraper(
            "https://www.gear4music.com/dj-equipment/scratch-dj/needles")

    def test_accept_cookies(self):
        self.scraper.accept_cookies()

        with self.assertRaises(NoSuchElementException):
            self.scraper.driver.find_element_by_xpath(
                "//button[@id='banner-cookie-consent-allow-all']")
        # check if the accept button still exists

    def test_retrieve_product_links(self):
        # checks the types are correct
        expected_type = list
        expected_url_type = str
        actual_value = self.scraper.retrieve_product_links(
            "https://www.gear4music.com/dj-equipment/scratch-dj/needles", 1)
        actual_type = type(actual_value)
        actual_url_type = type(actual_value[0])
        self.assertEqual(expected_type, actual_type)
        self.assertEqual(expected_url_type, actual_url_type)

    def tearDown(self):
        self.scraper.close_scraper()


class ScraperDataCollectionTestCase(unittest.TestCase):
    def setUp(self):
        self.scraper = Scraper(
            "https://www.gear4music.com/dj-equipment/scratch-dj/needles")
        self.reduced_sample_data = {
                "product_ref": "6476",
                "product_name": "Shure SM58 Dynamic Cardioid Vocal Microphone",
                "description": "Comments from customers who bought this item:\nFull Description\nThe microphone to beat\nYou\u2019ve heard the Shure SM58 a thousand times before. Tuned to deliver the warmth of your voice and project it over the crowds. It\u2019s ideal for lead singers, back-up singers, and public speakers.\nSince going on sale in 1966, the SM58 has become the industry standard. Designed from the very beginning for life on the road. It became famous for its toughness and steel mesh filter that reduces wind and \u2018pop\u2019 noises - it picks up your voice and nothing else.\nIconic vocal sound\nThe SM58 has a signature sound that was created for live music. Shure achieved it by boosting the mid-range. This little trick means it doesn\u2019t matter who uses it, their voice will cut through the mix.\nThe sound profile was also designed with a cardioid polar pattern and \u2018bass roll-off\u2019. This feature allows for the \u2018proximity effect\u2019 (increasing bass by moving closer to the mic) letting singers make changes to their vocal tone on the fly.\nThe clear sound is never interrupted either. The SM58 stops noise from vibrations and handling of the microphone, thanks to a built-in shock mount that protects the clarity of your voice.\nBuilt to last\nYou can expect the SM58 to withstand the wear and tear of touring. Shure went to great lengths to make sure the SM58 would still work, even after serious damage. Built from an all-metal construction, using heat and water-resistant adhesives, the microphone cartridge is protected to deliver years of great performance.\nYou can be confident of its durability - Shure tried freezing it, cooking it, and submerging it. They even dropped it from a 7-storey building and it still worked! Once you know that, you understand why it\u2019s the microphone The Rolling Stones go on tour with.\nAccept no imitation. Gear4music deals directly with Shure, all of our SM58's are certified genuine products.\nPress Reviews\nSurvey Winner 2009: Best Microphone - MI Pro\nReader's Choice Award 2009: Dynamic Microphones - ProSound\nIncluded In The Box\n1 x Shure SM58 Microphone\n1 x Zippered storage bag\n1 x Microphone clip\nSpecifications\nTransducer Type: Dynamic\nPolar Pattern: Cardioid\nFrequency response: 50Hz - 15kHz\nSensitivity: -54,5dBV/Pa / 1,88mV/Pa (@ 1kHz)\nImpedance: 150\u03a9 (300\u03a9 actual) for inputs rated low impedance\nDimensions: 162mm (6-3/8\") L x 51mm (2\") W\nWeight: 298g (10.5oz)\nA similar model is also available with the addition of an on/off switch - SM58S",
                "images": [
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479258/600/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479259/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479260/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479261/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479262/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479263/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/47/479264/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/23/231371/1200/preview.jpg",
                    "https://d1aeri3ty3izns.cloudfront.net/media/23/231359/1200/preview.jpg"
                ]
            }
        self.actual_data = self.scraper.collect_product_data(
            'https://www.gear4music.com/PA-DJ-and-Lighting/Shure-SM58-Dynamic-Cardioid-Vocal-Microphone/4ZW')

    def test_check_stock(self):
        stock = self.scraper.check_stock()
        self.assertEqual(type(stock), str)

    def test_check_sale(self):
        sale = self.scraper.check_sale()
        self.assertEqual(type(sale), bool)

    def test_collect_image_links(self):
        image_links = self.scraper.collect_image_links()
        self.assertEqual(type(image_links), list)
        self.assertEqual(type(image_links[0]), str)

    def test_collect_product_data(self):
        expected_value = self.reduced_sample_data
        actual_value = self.actual_data
        # removes the data which is likely to change
        actual_value.pop("price")
        actual_value.pop("stock")
        actual_value.pop("sale")
        actual_value.pop("product_uuid")
        self.assertDictEqual(expected_value, actual_value)

    def test_collect_product_data_and_store(self):
        self.scraper.collect_product_data_and_store(
            'https://www.gear4music.com/PA-DJ-and-Lighting/Shure-SM58-Dynamic-Cardioid-Vocal-Microphone/4ZW')
        # directories which should exist are
        assert os.path.exists(os.getcwd()+"/raw_data/6476/images")
        assert os.path.isfile(os.getcwd()+"/raw_data/6476/data.json")

    def tearDown(self):
        self.scraper.close_scraper()
        self.scraper.__delete_from_local_machine()


if __name__ == "__main__":
    unittest.main()
