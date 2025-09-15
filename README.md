## Installation (Linux)

1. **Clone the repository**

```bash
git clone https://github.com/oxagast/disscorders.git
cd disscorders
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama2-uncensored
ollama pull brxce/stable-diffusion-prompt-generator
pip install -r requirements.txt
python main.py
```
