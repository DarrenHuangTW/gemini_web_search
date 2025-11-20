# Gemini Web Search App 🔍

A Streamlit web application that leverages Google's Gemini AI with web search capabilities to process multiple prompts and provide comprehensive results with cited sources.

## Features ✨

- **Batch Processing**: Enter up to 50 prompts at once
- **Google Search Integration**: Automatic web search grounding for relevant queries
- **Comprehensive Results**: View original prompts, search queries, and responses
- **Table Display**: Clean, organized table view with key metrics
- **Downloadable Reports**: Export results in CSV or JSON format
- **Real-time Processing**: Progress tracking with visual feedback

## Installation 🚀

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/gemini-web-search-app.git
   cd gemini-web-search-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Get your Google AI API key:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create and copy your API key

## Usage 💻

1. Start the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

2. Open your browser to `http://localhost:8501`

3. Enter your Google AI API key in the sidebar

4. Add your prompts (one per line) and click "Process Prompts"

5. View results in the table and download as needed

## Output Format 📊

### Table Display
- **ID**: Sequential result number
- **Original Prompt**: Your input query
- **Search Used**: Whether Google search was utilized
- **# Queries**: Number of web search queries made
- **Web Search Queries**: List of actual search terms used
- **Final Response**: AI response (truncated to 300 characters)

### Download Files
Complete data including:
- All table data plus full response text
- Cited source URLs and titles
- Detailed search query information

## Example Prompts 📝

```
What's the latest news about AI?
Who's Michael Jackson?
What is the capital of Taiwan?
How many centimeters is one meter?
Hi how are you?
```

## Requirements 📋

- Python 3.7+
- Streamlit
- Google GenerativeAI library
- Pandas
- Valid Google AI API key

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Note 🔒

Never commit your API key to version control. The app requires you to enter it securely through the interface.

## Support 💬

If you encounter any issues or have questions, please open an issue on GitHub.

---

Built with ❤️ using Streamlit and Google's Gemini AI