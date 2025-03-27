# Algo Trading and Financial News Sentiment Analysis

## Overview
This project integrates algorithmic trading strategies with financial news sentiment analysis to enhance decision-making in trading. The system processes real-time financial news, analyzes sentiment, and incorporates insights into an AI-driven trading strategy.

## Features
- **Algorithmic Trading Strategy**: Implements a trend-based signal strategy.
- **Sentiment Analysis**: Extracts and analyzes news sentiment for trading decisions.
- **Real-time Data Processing**: Fetches live BTC/USDT market data.
- **Web Application**: User-friendly dashboard to visualize market trends and sentiment analysis.
- **AI-driven Decision Making**: Uses machine learning to refine trading signals.

## Technologies Used
- **Backend**: Python, FastAPI, WebSockets
- **Frontend**: HTML, CSS, JavaScript
- **Machine Learning**: NLP for sentiment analysis
- **Database**: SQLite / PostgreSQL
- **APIs**: TradingView, Financial News APIs

## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (`venv` or `conda`)
- API keys for TradingView and financial news sources

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/tejask0512/Algo-trading-and-Financial-News-Sentiment-Analysis.git
   cd Algo-trading-and-Financial-News-Sentiment-Analysis
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up API keys and Tokens in `.env` file:
   ```env
   HuggingFace_token=your_hugging_face_token
   ```

5. Run the application:
   ```bash
   python main.py
   ```

6. Change the Path in 'config.py' and 'scraper.py' file:
   ```bash
   Data_DIR=''
   ```

## Usage
- Access the web application at `http://localhost:8000`
- Monitor live BTC/USDT price trends
- View sentiment analysis of financial news
- Analyze algorithmic trading signals

## Roadmap
- Implement multi-asset trading support
- Enhance sentiment model accuracy
- Deploy to cloud for real-time trading

## Contribution
Contributions are welcome! Fork the repo and submit a PR.

## License
This project is licensed under the MIT License.

## Contact
- **Author**: Tejas Kamble
- **Website**: [tejaskamble.com](https://tejaskamble.com)
- **GitHub**: [tejask0512](https://github.com/tejask0512)

