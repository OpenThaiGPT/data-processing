from data_processing.perplexity_filtering.perplexity import (
    classify_spam
)
import pandas as pd
from datasets import Dataset
import unittest

sample = [
    {
        "is_spam": 1,
        "doc": "สวัสดีจ๊ะ! วันนี้ขายส้มโอนะคะ ส้มโอสดป้ายแดง อร่อยมากค่า ดูมั่งมี้ทั้งภาพและวิดีโอลามกห้ามพลาดเด็ดขาดจร้า",
    },
    {
        "is_spam": 1,
        "doc": "สื่อลามกออนไลน์คุณภาพสูงสุด XXX69 ถ่ายทำเองโดยนางเอกจริงๆ พร้อมเบอร์ติดต่อสั่งซื้อ 088-123-4567 (นางสาวก๊กเอ้ย)",
    },
    {
        "is_spam": 1,
        "doc": "พลาดไม่ได้ ผลิตภัณฑ์อาหารเสริมดัชชี่วิตตาไก่ขาย 390 บาท ผสมน้ำเปล่าสำหรับผู้หญิง ไลน์ไอดีduchayfc สนใจสั่งซื้อด่วน",
    },
    {
        "is_spam": 1,
        "doc": "หนีความจริงได้ที่นี่ สิทธิพิเศษพนันบอลฟรีทั้งวัน เราให้เครดิตแรกเข้า 1,000 คะแนน 0-222-33444 (คุณก้อยนวล) กดวันนี้ด่วน",
    },
    {
        "is_spam": 1,
        "doc": "ในยามเช้าที่สดใส พร้อมแสงอรุณอันงดงามของดวงอาทิตย์ ฉันรู้สึกได้ถึงพลังสดชื่นและความหวังใหม่ที่จะเติมเต็มวันนี้ด้วยความสำเร็จและความสุขที่ยั่งยืน ช่างเป็นภาพที่สวยงามและทรงพลังจริงๆ ที่ได้ต้อนรับวันใหม่อันน่าตื่นเต้นนี้",
    },
    {"is_spam": 1, "doc": "สวัสดีวันจันทร์ ขอให้วันนี้เป็นวันที่สดใน"},
    {"is_spam": 1, "doc": "วันศุกร์แล้ว เลิกงานไปไหนกันดีทุกคน ไปทานข้าวกันไหม"},
    {"is_spam": 0, "doc": " "},
]

df_sample = pd.DataFrame({"text": sample})
ds_sample = Dataset.from_pandas(df_sample)


class TestPerplexity(unittest.TestCase):

    def test_classify_spam(self):
        assert (
            classify_spam(
                "คลิปหลุดคุณภาพสูงสุด XXX888 ถ่ายทำเองโดยนางเอกจริงๆ หมาลัยชื่อดัง"
            )[0]
            == 1
        )

    def test_classify_spam2(self):
        for text in sample:
            prediction, log_pp_score = classify_spam(text["doc"])
            print(prediction.item(), log_pp_score)
            assert prediction == text["is_spam"]

    def test_classify_spam_threshold(self):
        for text in sample:
            prediction, log_pp_score = classify_spam(text["doc"], 0.4)
            print(prediction.item(), log_pp_score)
            assert prediction == text["is_spam"]


if __name__ == "__main__":
    unittest.main()
