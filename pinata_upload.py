import requests

JWT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiIxMjVlOThlNS1mOTQ3LTRkZTItOGViZi0zYzUwMzA3OGUwNTgiLCJlbWFpbCI6ImFic3RyYWN0YXJ0Njk0MjA4OEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGluX3BvbGljeSI6eyJyZWdpb25zIjpbeyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJGUkExIn0seyJkZXNpcmVkUmVwbGljYXRpb25Db3VudCI6MSwiaWQiOiJOWUMxIn1dLCJ2ZXJzaW9uIjoxfSwibWZhX2VuYWJsZWQiOmZhbHNlLCJzdGF0dXMiOiJBQ1RJVkUifSwiYXV0aGVudGljYXRpb25UeXBlIjoic2NvcGVkS2V5Iiwic2NvcGVkS2V5S2V5IjoiMGMzY2ZmYWRlMzlmNDIzMzhkZjQiLCJzY29wZWRLZXlTZWNyZXQiOiI4YzM2ZWU0MmMzMjEyZTJiMGJkODUyNWNhZjY2OWFhZDEwNmM4MmMxODNjMTE0MjA1ZWE5ZDRmYzEyNmExNzc5IiwiZXhwIjoxODA2NjU1Nzc0fQ.qf6iXOMJhg2Gas_1adtdTqtxEWt4MTv3tpx-c_ad7Wg"


def upload_to_pinata(data, filename="data.txt"):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

    files = {"file": (filename, data)}

    headers = {"Authorization": f"Bearer {JWT_KEY}"}

    response = requests.post(url, files=files, headers=headers)
    return response.json()


if __name__ == "__main__":
    result = upload_to_pinata("Hello World test")
    print(result)
