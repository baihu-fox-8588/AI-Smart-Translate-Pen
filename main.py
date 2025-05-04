import logging

from rich.logging import RichHandler

icons = {
    'DEBUG': '[blue] ℹ [/blue]',
    'INFO': '[green] ✓ [/green]',
    'WARNING': '[yellow] ! [/yellow]',
    'ERROR': '[red] ✗ [/red]',
    'CRITICAL': '[red bold] ✗ [/red bold]',
    'SUCCESS': '[green bold] ✓ [/green bold]',
    'PENDING': '[blue] ⏳ [/blue]',
    'FAILED': '[red] ✗ [/red]'
}
    
class IconLogHandler(RichHandler):
    def render(self, record, message_renderable, traceback=None):
        icon = icons.get(record.levelname, '')
        if traceback is not None:
            return f"{message_renderable}\n{traceback}"
            
        message_str = str(message_renderable)
            
        time_str = message_str[:message_str.find(' -')]
        time_str = time_str.replace('[', '').replace(']', '')
        return f"{time_str} {icon} - {message_str[message_str.find('-')+1:].strip()}"
    
logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s - %(message)s",
    datefmt="%X",
    handlers=[IconLogHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=False
    )]
)
    
logger = logging.getLogger("rich")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

from google import genai

from typing import List, Literal
from pydantic import BaseModel

class RootWord(BaseModel):
    root: str
    meaning: str
    
class Example(BaseModel):
    sentence: str
    translation: str

class Word(BaseModel):
    Traditional_Chinese_Translation: str
    English_to_English_Translation: str
    Part_of_Speech: Literal['n', 'v', 'adj', 'adv', 'pron', 'prep', 'conj', 'interj', 'det', 'art']
    pronunciation: str
    root_word: list[RootWord]
    synonyms: list[str]
    antonyms: list[str]
    collocations: list[str]
    related_words: list[str]
    examples: list[Example]
    notes: list[str]

class WordList(BaseModel):
    words: List[Word]
    

from dotenv import load_dotenv
import os

load_dotenv()

try:
    client = genai.Client(api_key = os.getenv("GEMINI_API"))
    logger.info("Gemini 連線成功")
    
except Exception as e:
    logger.error(f"Gemini 連線失敗: {e}")
    raise e

prompt = """
你是一位專業的英語語言學家和詞典編纂者。你的任務是分析使用者提供的英文單字或片語生成詳細的資訊。

請遵循以下指示：

1.  **識別多重含義**：仔細分析輸入的單字或片語，判斷它是否有一個或多個不同的含義。
2.  **為每個含義生成獨立條目**：如果單字或片語有多個**顯著不同**的含義（例如，"bank" 作為金融機構和作為河岸），請為**每一個**不同的含義創建一個獨立的 `Word` JSON 物件。
3.  **合併相似含義**：如果不同的中文翻譯只是同一基本含義的不同說法（例如，「電腦」和「計算機」指 computer），請將它們合併到**單一個** `Word` 物件中。你可以在 `Traditional_Chinese_Translation` 中列出多個說法，或在 `notes` 中加以說明。
4.  **填充 `Word` 物件欄位**：對於每個 `Word` 物件，請準確填充所有欄位：
    *   `Traditional_Chinese_Translation`: 提供該特定含義對應的**繁體中文**翻譯。
    *   `English_to_English_Translation`: 提供該特定含義的清晰英文解釋。
    *   `Part_of_Speech`: 標明該特定含義的詞性。
    *   `pronunciation`: 提供標準的英文發音（例如 IPA）。
    *   `root_word`: 列出相關的詞根及其意義。
    *   `synonyms`: 提供該特定含義的同義詞列表。
    *   `antonyms`: 提供該特定含義的反義詞列表。
    *   `collocations`: 列出與該含義搭配的常見詞語。
    *   `related_words`: 列出相關的衍生詞或概念詞。
    *   `examples`: 提供至少兩個使用該特定含義的英文例句，並附上**繁體中文**翻譯。
    *   `notes`: 添加任何關於用法、語境、文化差異或其他值得注意的補充說明。
5.  **輸出格式**：最終輸出必須是一個符合 `WordList` schema 的 JSON 物件，其中 `words` 欄位是一個包含所有獨立 `Word` 物件的列表。

請確保所有提供的資訊都是準確且與單字的特定含義緊密相關的。
"""

def main(word: str, thinking_budget: int = 1024) -> WordList:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=word,
            config = {
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_schema": WordList,
                "system_instruction": prompt,
                "thinking_config": genai.types.ThinkingConfig(thinking_budget=thinking_budget)
            }
        )
        
        return response.text
    
    except Exception as e:
        logger.error(f"調用 Gemini 失敗: {e}")
        raise e

if __name__ == "__main__":
    try:
        while True:
            word = input("請輸入要查詢的單字或片語: ")
            print(main(word))
            
    except KeyboardInterrupt:
        logger.info("程式已中止")
        exit()
