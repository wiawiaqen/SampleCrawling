import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import os
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def extract_year(
    symbol: str, year: int, quarter: int, session: aiohttp.ClientSession
) -> dict:
    """
    Extract balance sheet data for a given symbol, year, and quarter.

    Args:
        symbol (str): Stock symbol to extract data for.
        year (int): Year of the financial data.
        quarter (int): Quarter of the financial data.
        session (aiohttp.ClientSession): The HTTP session to use for making requests.

    Returns:
        dict: Extracted balance sheet data.
    """
    url = f"https://s.cafef.vn/bao-cao-tai-chinh/{symbol}/bsheet/{year}/{quarter}/0/0/bao-cao-tai-chinh-.chn"
    async with session.get(url) as response:
        text = await response.text()
    soup = BeautifulSoup(text, "html.parser")

    trs = soup.select("tr.r_item, tr.r_item_a")
    data_dct = {}

    for tr in trs:
        values = tr.find_all("td")
        if values:
            data_dct[values[0].get_text(strip=True)] = [
                v.get_text(strip=True) for v in values[1:5]
            ]
    data_dct["Year"] = get_years(soup)

    return data_dct


def get_years(soup: BeautifulSoup) -> list:
    """
    Extract years from the given BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.

    Returns:
        list: List of years extracted from the HTML content.
    """
    years = soup.find_all("td", class_="h_t")
    return [year.get_text(strip=True) for year in years]


async def fetch_and_expand_data(
    symbol: str, start_year: int, end_year: int
) -> pd.DataFrame:
    """
    Fetch all balance sheet data for a given symbol and expand it into a DataFrame.

    Args:
        symbol (str): Stock symbol to fetch data for.
        start_year (int): Start year for the data extraction.
        end_year (int): End year for the data extraction.

    Returns:
        pd.DataFrame: DataFrame containing the expanded balance sheet data for the given symbol and year range.
    """
    timeout = aiohttp.ClientTimeout(total=300)
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = []
        for year in range(start_year, end_year + 1):
            tasks.append(extract_year(symbol, year, 1, session))

        data_list = await asyncio.gather(*tasks, return_exceptions=True)

    result = defaultdict(list)

    for d in data_list:
        if isinstance(d, Exception):
            print(f"Error fetching data: {d}")
            continue
        for key, value in d.items():
            result[key].extend(value)

    df = pd.DataFrame(dict(result))
    expanded_df = df.explode(list(df.columns.difference(["Year"])))
    return expanded_df


async def create_df_from_symbol(
    symbol: str, start_year: int, end_year: int
) -> pd.DataFrame:
    """
    Create a DataFrame from the balance sheet data of a given symbol.

    Args:
        symbol (str): Stock symbol to create DataFrame for.
        start_year (int): Start year for the data extraction.
        end_year (int): End year for the data extraction.

    Returns:
        pd.DataFrame: DataFrame containing the balance sheet data for the given symbol.
    """
    try:
        expanded_data = await fetch_and_expand_data(
            symbol.lower(), start_year, end_year
        )
        if not isinstance(expanded_data, pd.DataFrame):
            return pd.DataFrame()
        expanded_data["stock"] = symbol
        return expanded_data[expanded_data["A- TÀI SẢN NGẮN HẠN"].str.strip().ne("")]
    except Exception as e:
        print(f"Error creating dataframe for symbol {symbol}: {e}")
        return pd.DataFrame()


async def main():
    """
    Main function to execute the balance sheet data extraction and save to Excel.

    Raises:
        Exception: If there is an error reading stock symbols file.
    """
    current_dir = os.getcwd()
    files = [
        f
        for f in os.listdir(current_dir)
        if os.path.isfile(os.path.join(current_dir, f))
    ]

    symbols = []
    for f in files:
        if f == "stock.csv" or f == "stock.xlsx":
            try:
                if f.endswith(".xlsx"):
                    symbols = pd.read_excel(f)["stock"].tolist()
                else:
                    symbols = pd.read_csv(f)["stock"].tolist()
                break
            except Exception as ex:
                print(f"Error reading stock symbols file: {ex}")
                raise Exception("Error reading stock symbols file!")

    year_start = int(input("Enter start year: "))
    year_end = int(input("Enter end year: "))

    tasks = [create_df_from_symbol(s, year_start, year_end) for s in symbols]
    data_frames = await asyncio.gather(*tasks)

    data = pd.concat(data_frames)
    cols = ["stock", "Year"] + [
        col for col in data.columns if col not in ["stock", "Year"]
    ]
    data = data[cols]
    data.to_excel("balance_sheet.xlsx", index=False)


if __name__ == "__main__":
    asyncio.run(main())
