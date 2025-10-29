from flask import Flask
from flask_cors import CORS
import threading
from config import db

# Import all service blueprints
from services.login import login_bp
from services.register import register_bp
from services.get_quiz import get_quiz_bp
from services.submit_quiz import submit_quiz_bp
from services.get_quizzes import get_quizzes_bp
from services.create_quiz import create_quiz_bp
from services.get_users import get_users_bp
from services.verify_token import verify_token_bp
from services.decode_token import decode_token_bp
from services.dashboard import dashboard_bp
from services.quiz_info import quiz_info_bp
from services.update_quiz import update_quiz_bp
from services.delete_quiz import delete_quiz_bp
from services.delete_question import delete_question_bp

# Create Flask app
app = Flask(__name__)

# Configure CORS to support all localhost origins
# Using regex pattern to match localhost and 127.0.0.1 with http/https
CORS(app, 
     origins=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
     supports_credentials=True)

# Register all blueprints
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)
app.register_blueprint(get_quiz_bp)
app.register_blueprint(submit_quiz_bp)
app.register_blueprint(get_quizzes_bp)
app.register_blueprint(create_quiz_bp)
app.register_blueprint(get_users_bp)
app.register_blueprint(verify_token_bp)
app.register_blueprint(decode_token_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(quiz_info_bp)
app.register_blueprint(update_quiz_bp)
app.register_blueprint(delete_quiz_bp)
app.register_blueprint(delete_question_bp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify all services are running"""
    return {
        'status': 'healthy',
        'services': [
            'login',
            'register',
            'get_quiz',
            'submit_quiz',
            'get_quizzes',
            'create_quiz',
            'get_users',
            'verify_token',
            'decode_token',
        'dashboard',
        'quiz_info',
        'update_quiz',
        'delete_quiz',
        'delete_question'
    ],
        'database': 'connected' if db is not None else 'disconnected'
    }, 200

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Quiz Application with Microservices Architecture")
    print("=" * 60)
    print("\nAll services registered:")
    print("- Login Service")
    print("- Register Service")
    print("- Get Quiz Service")
    print("- Submit Quiz Service")
    print("- Get Quizzes Service")
    print("- Create Quiz Service")
    print("- Get Users Service")
    print("- Verify Token Service")
    print("- Decode Token Service")
    print("- Dashboard Service")
    print("- Quiz Info Service")
    print("- Update Quiz Service")
    print("- Delete Quiz Service")
    print("- Delete Question Service")
    print("\nHealth endpoint available at: /health")
    print(f"All services running on single port: 5000")
    print("=" * 60)
    

    app.run(host="0.0.0.0", port=5000)

