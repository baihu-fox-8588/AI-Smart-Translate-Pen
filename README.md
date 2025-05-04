# AI 智慧翻譯筆 (AI Smart Translate Pen)

這是一個使用 Google Gemini API 的 Python 工具，旨在提供詳細的英文單字或片語分析，並將其翻譯成繁體中文。它就像一本智慧詞典，能深入解釋單字的詞性、發音、詞根、同反義詞、搭配詞、相關詞、例句和補充說明。

## 功能

*   **詳細單字分析**: 接收英文單字或片語作為輸入。
*   **多重含義處理**: 針對具有多個顯著不同含義的單字，為每個含義生成獨立的解釋條目。
*   **豐富資訊**: 提供包含繁體中文翻譯、英文解釋、詞性、發音 (IPA)、詞根、同反義詞、搭配詞、相關詞、例句（附中文翻譯）及補充說明的詳細資訊。
*   **JSON 輸出**: 以結構化的 JSON 格式輸出分析結果。
*   **輸入方式**:
    *   **手動輸入**: 在終端機中直接輸入要查詢的單字或片語。
    *   **(計劃中) 自動擷取**: 未來計劃支援類似 Ctrl+F 的功能，自動獲取當前選取的文字。
*   **(計劃中) 結果儲存**: 未來計劃將查詢結果儲存到指定的資料夾中。

## 環境需求

*   Python 3.8 或更高版本
*   pip (Python 套件管理器)

## 安裝

1.  **複製儲存庫**:
    ```bash
    git clone <your-repository-url>  # 請將 <your-repository-url> 替換成您的儲存庫 URL
    cd <your-repository-directory> # 請將 <your-repository-directory> 替換成您的專案目錄名稱
    ```
2.  **建立虛擬環境** (建議):
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```
3.  **安裝依賴套件**:
    您需要先建立一個 `requirements.txt` 檔案，包含專案所需的套件。根據您目前的 `main.py`，至少需要以下套件：
    ```txt
    # requirements.txt
    google-generativeai
    pydantic
    python-dotenv
    rich
    ```
    然後執行安裝指令：
    ```bash
    pip install -r requirements.txt
    ```

## 設定

1.  **取得 Google Gemini API 金鑰**: 前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 取得您的 API 金鑰。
2.  **設定環境變數**:
    *   在專案的根目錄下建立一個名為 `.env` 的檔案。
    *   在 `.env` 檔案中加入以下內容，將 `<YOUR_GEMINI_API_KEY>` 替換成您實際的 API 金鑰：
        ```dotenv
        # .env
        GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
        ```
    *   **重要**: 請檢查您的 `main.py` 檔案第 82 行。根據您提供的錯誤訊息，您在 `.env` 檔案中使用的變數名稱可能是 `GEMINI_API_KEY`，但在程式碼中您使用的是 `os.getenv("GEMINI_API")`。請確保程式碼中的 `os.getenv()` 函數讀取的環境變數名稱與您在 `.env` 檔案中設定的名稱**完全一致**。建議將 `main.py` 第 82 行修改為：
        ```python
        client = genai.Client(api_key = os.getenv("GEMINI_API_KEY"))
        ```

## 使用方法

1.  **執行腳本**:
    ```bash
    python main.py
    ```
2.  **輸入查詢**:
    *   程式會提示您 `請輸入要查詢的單字或片語:`。
    *   輸入您想查詢的內容後按 Enter。
3.  **檢視結果**:
    *   分析結果會以 JSON 格式直接輸出到終端機。
    *   按 `Ctrl+C` 可以中止程式。

## 輸出

目前，分析結果會直接顯示在終端機中。未來的版本會將結果儲存為檔案於指定資料夾。
