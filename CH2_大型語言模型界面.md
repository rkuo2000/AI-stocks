## CH2. 大型語言模型界面

---
### Cloud platform

#### [Kaggle](https://www.kaggle.com/)

#### [Colab](https://colab.research.google.com/)

---
### [OpenAI](https://openai.com/)
* [Documentations](https://platform.openai.com/docs/overview)
`pip install openai` <br>
* [API reference](https://platform.openai.com/docs/api-reference/authentication)

---
### [Google AI Studio](https://aistudio.google.com)
[Gemini API Key](https://aistudio.google.com/apikey)<br>

#### [Gemini 模型](https://ai.google.dev/gemini-api/docs/models?hl=zh-tw)
**Gemini 2.5 Pro**<br>
我們最先進的思考模型，能夠推論程式碼、數學和 STEM 領域的複雜問題，也能使用長篇脈絡資料分析大型資料集、程式碼集和文件。<br>
**Gemini-2.5-flash**<br>
在性價比方面表現最佳，提供全方位功能。2.5 Flash 最適合用於大規模處理、低延遲、需要思考的大量工作，以及代理程式應用實例。<br>

`pip install google.generativeai`<br>

```
import google.generativeai as genai
import os

api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_Key)

model = genai.GenerativeModel("gemini-2.5-flash")

prompt = "What is LLM reasoning?"

results = model.generate_content([prompt])
print(results.text)
```
---
### [https://aistudio.google.com/apps](https://aistudio.google.com/apps)
