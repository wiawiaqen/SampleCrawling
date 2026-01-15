import json
import aiohttp
import asyncio
import html
import bs4

url = "https://vietstock.vn/StartPage/ChannelContentPage"

headers = {
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://vietstock.vn",
    "Referer": "https://vietstock.vn/chung-khoan/co-phieu.htm",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

cookies = {
    "_ga": "GA1.1.560614015.1768461525",
    "_pbjs_userid_consent_data": "3524755945110770",
    "isShowLogin": "true",
    "_cc_id": "1faf7a6050fd4bc3b5390d359e97b979",
    "panoramaId_expiry": "1769066328384",
    "panoramaId": "6fa8cd87b7e6029b64babf4f13cf16d539385a095681796b8f2432cd2de39f8e",
    "panoramaIdType": "panoIndiv",
    "ASP.NET_SessionId": "huml4mlfylovdwy1k2ucxf3w",
    "__RequestVerificationToken": "n93Zcw29l4ENkL-pR5kV52XS6QrScxd3xtlA76hSl_5Dgu1YsQ9PMIPbco7B-hi6GManziI5102D758yiijwBYDPMhxSdRtfdIMD003l2v41",
    "cto_bidid": "UGkMxV9IUDJqJTJGZzNKVG5oeUpWJTJGZlA5bFBTQWt5eiUyQk83ekVUODg1bHUxYmhpVGQ5d1RmVm0yMnRCd0UlMkJzaGdTMDBRQzRYRXJFVGZMUDFDU29sTlpJMFlTZXFQYSUyQnZjQjIwY1VVekpQbE1FV05QWTAlM0Q",
    "_ga_EXMM0DKVEX": "GS2.1.s1768467204$o2$g1$t1768467205$j59$l0$h0",
    "cto_dna_bundle": "8pTew18wcjVrNDRKRmU5WW4wTHhScW1jYjBoaHRMR01DNmJCS1lYR01Bdk4zbkt2T3R6S3JpakdpejVrWGh3b1NLT09kT081cjVYY1lXUkMxTEVoRkMwZEh3QSUzRCUzRA",
    "FCCDCF": "%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5B32%2C%22%5B%5C%222085fbc8-006d-4cea-8c43-d8181ec7dc02%5C%22%2C%5B1768461526%2C840000000%5D%5D%22%5D%5D%5D",
    "FCNEC": "%5B%5B%22AKsRol_2YfxeXFp9WPviiKjbjGBSD9PHe7Pd3ayNXSPF1HivWHlZ6sQsK9hXmdnVneoA7xrV-58pH8yYsno_ygdpwQZ2ZdLeXfw77bFp1mcsvjZWA5Voyhdwr1OYVsMzy-hAOGkNbLs1yBL2_CYam6oRgYiy8IKyeg%3D%3D%22%5D%5D",
    "cto_bundle": "wMqDCF8wcjVrNDRKRmU5WW4wTHhScW1jYjBwRVAzQ3RsRHk3RlY0QUIlMkI5bEZsbUM1SEZPbWl2UHpBUVk2dXo0V3V3biUyRm03RkJtRFhwJTJCaTgyTENOdDdZWXN0ekF3RHhJMkhxV1R1Q0dLQk1YOGdxQkZvZldCaGhnVEZvVDVuMmY3bHZWeWNhQjYlMkYwM3A2OWZDUDB1RkJHM3NoZyUzRCUzRA",
    "__gads": "ID=fbf350dc916b98aa:T=1768461527:RT=1768467227:S=ALNI_Mams4FxkYgD84ssgI6M6AlHZR0vMQ",
    "__gpi": "UID=000011e4a23f54fd:T=1768461527:RT=1768467227:S=ALNI_MYk_iThXp29ux1iiRmY8M4XZJBoaw",
    "__eoi": "ID=400e603a5cc7aeff:T=1768461527:RT=1768467227:S=AA-AfjbFcT5JCV67yfvkhJ5gOzro",
}


def extract_data_from_html(soup: bs4.BeautifulSoup) -> list[dict]:
    """
    Extract data from html.

    Args:
        soup (bs4.BeautifulSoup): data

    Returns:
        list[dict]: extracted data
    """
    results = []
    posts = soup.find_all("div", class_="single_post_text")
    for post in posts:
        data = {}
        data["title"] = html.unescape(post.find("h4").text.strip())
        data["text"] = html.unescape(post.find("p", class_="post-p").text.strip())
        data["href"] = post.find("h4").find("a")["href"]
        results.append(data)
    return results


async def fetch_page(session: aiohttp.ClientSession, page: int) -> str:
    data = {"channelID": "830", "page": str(page)}
    async with session.post(
        url, headers=headers, cookies=cookies, data=data
    ) as response:
        content = await response.text()
        print(f"Fetched page {page} with status {response.status}")
        return content


async def fetch_all_pages(total_pages: int) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, total_pages + 1):
            tasks.append(fetch_page(session, page))
        pages_content = await asyncio.gather(*tasks)

        all_results = []
        for content in pages_content:
            soup = bs4.BeautifulSoup(content, "html.parser")
            page_results = extract_data_from_html(soup)
            all_results.extend(page_results)
        return all_results


async def main():
    total_pages = 50
    results = await fetch_all_pages(total_pages)
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
