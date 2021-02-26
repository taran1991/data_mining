import requests
import time
import json

from pathlib import Path


class Parse5ka:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0)"
        " Gecko/20100101 Firefox/85.0",
    }

    def __init__(self, start_url: str, products_path: Path):
        self.start_url = start_url
        self.products_path = products_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.products_path.joinpath(f"{product['id']}.json")
            self._save(product, product_path)

    def _parse(self, url):
        while url:
            response = self._get_response(url)
            data = response.json()
            url = data["next"]
            for product in data["results"]:
                yield product

    @staticmethod
    def _save(data: dict, file_path: Path):
        jdata = json.dumps(data, ensure_ascii=False)
        file_path.write_text(jdata, encoding="UTF-8")


class Parse5kaByCategories(Parse5ka):
    params = {"records_per_page": 20, "page": 1, "categories": None}

    def __init__(self, cat_url: str, start_url: str, products_path: Path):
        self.categories_url = cat_url
        super().__init__(start_url, products_path)

    def _get_categories(self):
        response = self._get_response(self.categories_url)
        categories = response.json()
        return categories

    def parse_by_categories(self):
        categories = self._get_categories()
        for category in categories:
            category_dict = {
                "code": category["parent_group_code"],
                "name": category["parent_group_name"],
                "products": [],
            }
            self.params["categories"] = category["parent_group_code"]
            request = requests.Request("GET", self.start_url, params=self.params).prepare()
            for product in self._parse(request.url):
                category_dict["products"].append(product)
            category_path = self.products_path.joinpath(
                f"category_{category['parent_group_code']}.json"
            )
            self._save(category_dict, category_path)


if __name__ == "__main__":
    products_url = "https://5ka.ru/api/v2/special_offers/"
    categories_url = "https://5ka.ru/api/v2/categories/"
    categories_path = Path(__file__).parent.joinpath("categories")
    if not categories_path.exists():
        categories_path.mkdir()
    parser = Parse5kaByCategories(categories_url, products_url, categories_path)
    parser.parse_by_categories()
