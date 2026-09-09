About the Application

MultiMeet Notes converts multilingual meeting recordings into English summaries, speaker-level transcripts, action items, and structured meeting insights.
About the Application
MultiMeet Notes is an AI-powered application that turns meeting recordings into clear and organized notes. A user uploads an audio file, and the application detects the spoken language, transcribes the meeting, identifies different speakers, creates an English summary, extracts action items, and displays the complete transcript with useful statistics.
It uses Streamlit for the interface, AssemblyAI for transcription and speaker diarization, and OpenAI for meeting analysis.

What the Application Does
- Detects the language spoken in the meeting
- Converts meeting audio into text
- Identifies different speakers using speaker diarization
- Generates an English meeting summary
- Extracts action items, assignees, due dates, and priorities when available
- Displays the full transcript with timestamps and statistics
- Allows users to download meeting notes as a Markdown file

Steps to Replicate
1. Install Python and uv: Install Python 3.9 or newer and uv.
2. Open the project folder: Confirm app.py, pyproject.toml, and src are present.
3. Install dependencies: Run: uv sync
4. Get API keys: Create AssemblyAI and OpenAI API keys.
5. Run the application: Run: uv run python -m streamlit run app.py
6. Enter the API keys: Add both keys in the left sidebar.
7. Upload a meeting recording: Use MP3, WAV, M4A, MP4, WEBM, or FLAC.
8. Start processing: Click Start Processing.
9. Review the results: Check language, summary, speakers, action items, transcript, and statistics.
10. Download the notes: Use Download as Markdown to save the results.

Main Commands
Install dependencies: uv sync
Run the application: uv run python -m streamlit run app.py


<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/b9a3e66a-c6a4-4670-8d5f-966fb1a6333c" />
