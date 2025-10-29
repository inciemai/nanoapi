from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from config import db
from utils.auth import admin_required

create_quiz_bp = Blueprint('create_quiz', __name__)

@create_quiz_bp.route('/quiz', methods=['POST'])
@admin_required
def create_quiz():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        
        # Get admin user info from token
        admin_user = request.current_user
        created_by = admin_user.get('name', 'Administrator')
        
        # Require title and questions array
        if 'title' not in data or not data['title']:
            return jsonify({'status': False, 'error': 'title is required'}), 400
        
        if 'questions' not in data or not data['questions']:
            return jsonify({'status': False, 'error': 'questions array is required'}), 400
        
        title = data['title']
        questions = data['questions']
        
        # Validate questions
        if not isinstance(questions, list) or len(questions) == 0:
            return jsonify({'status': False, 'error': 'Questions must be a non-empty array'}), 400
        
        # Validate each question - only require question, options, and correct_answer
        for idx, question in enumerate(questions):
            if 'question' not in question or not question['question']:
                return jsonify({'status': False, 'error': f'Question {idx + 1} must have question field'}), 400
            
            if 'options' not in question or not isinstance(question['options'], list) or len(question['options']) < 2:
                return jsonify({'status': False, 'error': f'Question {idx + 1} must have at least 2 options'}), 400
            
            if 'correct_answer' not in question or question['correct_answer'] not in question['options']:
                return jsonify({'status': False, 'error': f'Question {idx + 1} must have a correct_answer that matches one of the options'}), 400
        
        # Add unique IDs to each question
        for question in questions:
            question['question_id'] = str(ObjectId())
        
        # Create quiz document with simplified question format
        quiz_doc = {
            'title': title,
            'questions': questions,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'total_questions': len(questions)
        }
        
        # Insert into MongoDB
        result = db.quizzes.insert_one(quiz_doc)
        
        # Prepare questions response with IDs (without correct_answer for security)
        questions_response = []
        for question in questions:
            question_item = {
                'question_id': question['question_id'],
                'question': question['question'],
                'options': question['options']
            }
            questions_response.append(question_item)
        
        return jsonify({
            'status': True,
            'message': 'Quiz created successfully',
            'data': {
                'quiz_id': str(result.inserted_id),
                'title': title,
                'total_questions': len(questions),
                'created_by': created_by,
                'created_at': quiz_doc['created_at'],
                'questions': questions_response
            }
        }), 201
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

