import requests
import json
import urllib.parse

# 1. Điền Token bạn lấy từ giao diện Cube (chỗ "Authorization" trên ảnh màn hình)
# Ví dụ: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.W95DvPBfJQit4j9fleixSzdDz5M0bEx7cLmXrSIsu44"

def query_semantic_layer():
    # 2. Xây dựng câu hỏi (Query) dưới dạng JSON
    # Đây chính là sức mạnh của Headless BI: Hỏi bằng JSON!
    query = {
        "measures": [
            "fact_price_snapshots.count",                 # Lấy tổng số lượt bắt giá
            "fact_price_snapshots.average_sale_price"     # Lấy giá bán trung bình
        ],
        "dimensions": [
            "dim_platform.platform_name"                  # Chia (Group by) theo Tên Sàn TMĐT
        ]
    }

    # 3. Mã hóa Query thành URL (theo chuẩn của Cube REST API)
    encoded_query = urllib.parse.quote(json.dumps(query))
    url = f"http://localhost:4000/cubejs-api/v1/load?query={encoded_query}"
    
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }

    print(f"\n[INFO] Dang gui cuc JSON yeu cau toi Cube Semantic Layer...")
    response = requests.get(url, headers=headers)

    # 4. In kết quả đẹp đẽ ra màn hình
    if response.status_code == 200:
        data = response.json()
        print("\n--- DU LIEU TRA VE (JSON) SAN SANG CHO REACTJS/VUEJS ---")
        print(json.dumps(data['data'], indent=4, ensure_ascii=False))
    else:
        print(f"\n[ERROR] Loi: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    if TOKEN == "HAY_COPY_TOKEN_TU_GIAO_DIEN_VA_DAN_VAO_DAY":
        print("[ERROR] Ban chua chep Token tu giao dien web localhost:4000 vao bien TOKEN dong so 6 kia!")
    else:
        query_semantic_layer()
