import requests
from utils.error_data import LocationDataError


URL, key = "https://data-api.oxilor.com/rest/search-regions?", "cpkb-K_tkaEm4tIhwMMn4-AiDg8HfW"


def search_location(location):
    response = requests.get(URL + "searchTerm=" + location + "&type=city&first=10",
                            headers={"Authorization": f"Bearer {key}", "Accept-Language": "ru;en"})
    if response.status_code == 200:
        return response.json()
    else:
        raise LocationDataError("Возникла непредвиденная ошибка во время получения данных с data-api.oxilor.com. Status code: " +
                                str(response.status_code) + f". url: {response.url}")
