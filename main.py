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
import numpy as np
import json

from typing import List, Literal, Dict
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

class VectorEntry(BaseModel):
    path: str
    filename: str
    vector: list[float]

# 向量儲存路徑
VECTOR_STORAGE_PATH = r"C:\Users\baihu\OneDrive\Documents\obsidian\.obsidian\plugins\vector-search\vectors.json"

def load_vectors() -> List[VectorEntry]:
    """載入向量資料"""
    if os.path.exists(VECTOR_STORAGE_PATH):
        try:
            with open(VECTOR_STORAGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 確保資料是列表格式
                if not isinstance(data, list):
                    logger.warning("向量資料格式不正確，將重新初始化")
                    return []
                # 驗證每個條目的格式
                vectors = []
                for entry in data:
                    try:
                        if isinstance(entry, dict) and all(k in entry for k in ['path', 'filename', 'vector']):
                            vectors.append(VectorEntry(**entry))
                        else:
                            logger.warning(f"跳過無效的向量條目: {entry}")
                    except Exception as e:
                        logger.warning(f"處理向量條目時發生錯誤: {e}")
                return vectors
        except Exception as e:
            logger.error(f"載入向量資料時發生錯誤: {e}")
            return []
    return []

def save_vectors(vectors: List[VectorEntry]):
    """儲存向量資料"""
    try:
        os.makedirs(os.path.dirname(VECTOR_STORAGE_PATH), exist_ok=True)
        with open(VECTOR_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump([vector.model_dump() for vector in vectors], f, ensure_ascii=False, indent=2)
        logger.info("向量資料已成功儲存")
    except Exception as e:
        logger.error(f"儲存向量資料時發生錯誤: {e}")

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

def get_embedding(text: str) -> list[float]:
    try:
        result = client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=text
        )
        return [float(x) for x in result.embeddings[0].values]
    except Exception as e:
        logger.error(f"生成向量失敗: {e}")
        return []

def main(word: str, thinking_budget: int = 1024) -> str:
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
        
        word_list = WordList.model_validate_json(response.text)
        vectors = load_vectors()
        
        markdown = []
        for i, word_obj in enumerate(word_list.words):
            # 生成向量並儲存
            embedding = get_embedding(word_obj.English_to_English_Translation)
            
            # 建立檔案路徑
            filename = f"{word.lower()}.md"
            full_path = f"English/單字/{filename}"
            
            # 新增向量條目
            vectors.append(VectorEntry(
                path=full_path,
                filename=word_obj.Traditional_Chinese_Translation,
                vector=embedding
            ))
            
            # 添加 Obsidian 標籤
            markdown.append(f"# {word_obj.Traditional_Chinese_Translation}\n\n")
            
            # 英文解釋使用 callout
            markdown.append("> [!NOTE] 英文解釋\n")
            markdown.append(f"> {word_obj.English_to_English_Translation}\n\n")
            
            # 基本資訊區塊
            markdown.append("## 基本資訊\n\n")
            markdown.append(f"**詞性**：{word_obj.Part_of_Speech}\n")
            markdown.append(f"**發音**：`{word_obj.pronunciation}`\n\n")
            
            # 詞根資訊
            if word_obj.root_word:
                markdown.append("## 詞源分析\n\n")
                for root in word_obj.root_word:
                    markdown.append(f"### {root.root}\n")
                    markdown.append(f"> {root.meaning}\n\n")
            
            # 詞彙關係區塊
            markdown.append("## 詞彙關係\n")
            
            if word_obj.synonyms:
                markdown.append("### 同義詞\n")
                markdown.append("".join([f"- [[{synonym}]]\n" for synonym in word_obj.synonyms]))
            
            if word_obj.antonyms:
                markdown.append("### 反義詞\n")
                markdown.append("".join([f"- [[{antonym}]]\n" for antonym in word_obj.antonyms]))
            
            if word_obj.collocations:
                markdown.append("### 搭配詞\n")
                markdown.append("".join([f"- {collocation}\n" for collocation in word_obj.collocations]))
            
            if word_obj.related_words:
                markdown.append("### 相關詞\n")
                markdown.append("".join([f"- [[{related_word}]]\n" for related_word in word_obj.related_words]))
            
            # 例句區塊
            if word_obj.examples:
                markdown.append("## 例句\n\n")
                for example in word_obj.examples:
                    markdown.append("> [!example] 例句\n")
                    markdown.append(f"> {example.sentence}\n")
                    markdown.append(f"> \n")
                    markdown.append(f"> {example.translation}\n\n")
            
            # 備註區塊
            if word_obj.notes:
                markdown.append("## 備註\n\n")
                for note in word_obj.notes:
                    markdown.append("> [!tip] 補充說明\n")
                    markdown.append(f"> {note}\n\n")
            
            # 如果不是最後一個單字，才添加分隔線
            if i < len(word_list.words) - 1:
                markdown.append("---\n\n")
        
        # 儲存更新後的向量
        save_vectors(vectors)
        
        return "".join(markdown)
    
    except Exception as e:
        logger.error(f"調用 Gemini 失敗: {e}")
        raise e

if __name__ == "__main__":
    try:
        while True:
            word = input("請輸入要查詢的單字或片語: ")
            result = main(word)
            print(result)
            
            # 將結果儲存為 .md 檔案
            filename = f"{word.lower()}.md"
            with open(f"C:\\Users\\baihu\\OneDrive\\Documents\\obsidian\\English\\單字\\{filename}", "w", encoding="utf-8") as f:
                f.write(result)
            logger.info(f"已將結果儲存至 {filename}")
            
    except KeyboardInterrupt:
        logger.info("程式已中止")
        exit()
