from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from config import db
from utils.auth import token_required

submit_quiz_bp = Blueprint('submit_quiz', __name__)

@submit_quiz_bp.route('/quiz/<quiz_id>/submit', methods=['POST'])
@token_required
def submit_quiz(quiz_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'status': False, 'error': 'Invalid quiz ID'}), 400
        
        # Get quiz from database
        quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        
        if not quiz:
            return jsonify({'status': False, 'error': 'Quiz not found'}), 404
        
        data = request.get_json()
        
        # Validate questions format with question_id
        if 'questions' not in data or not isinstance(data['questions'], list):
            return jsonify({'status': False, 'error': 'Questions must be provided as an array'}), 400
        
        questions_data = data['questions']
        user_id = request.current_user.get('user_id')  # Get from token
        
        # Get username from database
        user = db.users.find_one({'_id': ObjectId(user_id)})
        username = user.get('name', '') if user else ''
        
        # Create a dictionary to map question_id to user answers and calculate total time
        user_answers_dict = {}
        time_taken = 0
        total_answered_questions = 0
        
        for question_item in questions_data:
            if 'question_id' in question_item:
                question_id = question_item['question_id']
                answer = question_item.get('answer', '')
                answered = question_item.get('answered', True)  # Default to True if not provided
                question_time = question_item.get('time_taken', 0)
                
                # Add up individual question times
                if isinstance(question_time, (int, float)) and question_time > 0:
                    time_taken += question_time
                
                # Count answered questions and store answers
                if answered:
                    total_answered_questions += 1
                    if answer:
                        user_answers_dict[question_id] = answer
        
        # Score the quiz
        correct_count = 0
        total_questions = len(quiz['questions'])
        questions_with_answers = []
        
        # Process each question from the quiz
        for question in quiz['questions']:
            question_id = question.get('question_id')
            user_answer = user_answers_dict.get(question_id) if question_id else None
            
            # Compare answers case-insensitively
            is_correct = False
            if user_answer is not None:
                is_correct = str(user_answer).strip().lower() == str(question['correct_answer']).strip().lower()
            
            if is_correct:
                correct_count += 1
            
            # Prepare question with user's answer and correctness
            question_response = {
                'question_id': question_id,
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'user_answer': user_answer if user_answer is not None else '',
                'is_correct': is_correct
            }
            questions_with_answers.append(question_response)
        
        # Store result
        result_doc = {
            'quiz_id': quiz_id,
            'user_id': user_id,
            'username': username,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'time_taken': time_taken,
            'questions': questions_with_answers,
            'submitted_at': datetime.now().isoformat()
        }
        
        db.quiz_results.insert_one(result_doc)
        
        return jsonify({
            'status': True,
            'message': 'Quiz submitted successfully',
            'result': {
                'correct_answers': correct_count,
                'total_questions': total_questions,
                'total_answered_questions': total_answered_questions,
                'time_taken': time_taken
            },
            'total_time_taken': time_taken,
            'questions': questions_with_answers
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

