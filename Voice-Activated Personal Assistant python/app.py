import threading
from flask import Flask, request, jsonify, render_template
import speech_recognition as sr
import pyttsx3
import requests
import queue

app = Flask(__name__)
engine = pyttsx3.init()
recognizer = sr.Recognizer()
reminders = []
speech_queue = queue.Queue()

# Function to convert text to speech
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function for handling voice recognition in a separate thread
def recognize_speech():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("Listening now...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"Command: {command}")
            speech_queue.put(command)  # Put command in queue for later use
        except sr.UnknownValueError:
            speech_queue.put("Sorry, I could not understand your command.")
        except sr.RequestError:
            speech_queue.put("Sorry, there was an issue with the speech service.")

# Route for the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle voice input
@app.route('/process_voice', methods=['POST'])
def process_voice():
    try:
        # Run the speech recognition in a separate thread
        voice_thread = threading.Thread(target=recognize_speech)
        voice_thread.start()
        # Send a temporary response while waiting for the result
        return jsonify({"status": "Listening... Please wait for processing."})
    except Exception as e:
        return jsonify({"error": str(e)})

# Route to fetch the result of speech processing
@app.route('/get_command_result', methods=['GET'])
def get_command_result():
    if not speech_queue.empty():
        command = speech_queue.get()
        return jsonify({"command": command})
    else:
        return jsonify({"status": "No command processed yet."})

# Route to set reminders
@app.route('/set_reminder', methods=['POST'])
def set_reminder():
    data = request.json
    reminder = data.get('reminder')
    reminders.append(reminder)
    speak("Reminder added.")
    return jsonify({"status": "success", "reminders": reminders})

# Route to fetch weather
@app.route('/get_weather', methods=['POST'])
def get_weather():
    data = request.json
    city = data.get('city')
    api_key = "46f1c46ccc8bac8036819f33e0bb6ff3"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url).json()
    if response.get("main"):
        temp = response["main"]["temp"]
        description = response["weather"][0]["description"]
        speak(f"The weather in {city} is {temp} degrees with {description}.")
        return jsonify({"temperature": temp, "description": description})
    else:
        speak("Sorry, I couldn't fetch the weather.")
        return jsonify({"error": "City not found"})

# Route to fetch news
@app.route('/get_news', methods=['GET'])
def get_news():
    api_key = "1c47ff90500c44588f74f0f8bafc7048"
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    response = requests.get(url).json()
    articles = response.get("articles", [])[:5]
    news = [{"title": article["title"], "description": article["description"]} for article in articles]
    speak("Here are the top headlines.")
    return jsonify({"news": news})

if __name__ == "__main__":
    app.run(debug=True)
