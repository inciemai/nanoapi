from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from config import db
from utils.auth import admin_required

update_quiz_bp = Blueprint('update_quiz', __name__)

@update_quiz_bp.route('/quiz/<quiz_id>', methods=['PUT'])
@admin_required
def update_quiz(quiz_id):
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Validate ObjectId
        if not ObjectId.is_valid(quiz_id):
            return jsonify({'status': False, 'error': 'Invalid quiz ID'}), 400
        
        # Check if quiz exists
        existing_quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        if not existing_quiz:
            return jsonify({'status': False, 'error': 'Quiz not found'}), 404
        
        data = request.get_json()
        
        # Get admin user info from token
        admin_user = request.current_user
        
        # Build update document - only update fields that are provided
        update_fields = {}
        
        if 'title' in data:
            if not data['title']:
                return jsonify({'status': False, 'error': 'title cannot be empty'}), 400
            update_fields['title'] = data['title']
        
        if 'questions' in data:
            new_questions = data['questions']
            
            # Validate questions if provided
            if not isinstance(new_questions, list) or len(new_questions) == 0:
                return jsonify({'status': False, 'error': 'Questions must be a non-empty array'}), 400
            
            # Get existing questions from the quiz
            existing_questions = existing_quiz.get('questions', [])
            
            # Validate and add new questions
            for idx, question_data in enumerate(new_questions):
                # Validate required fields
                if 'question' not in question_data or not question_data['question']:
                    return jsonify({'status': False, 'error': f'Question {idx + 1} must have question field'}), 400
                
                if 'options' not in question_data or not isinstance(question_data['options'], list) or len(question_data['options']) < 2:
                    return jsonify({'status': False, 'error': f'Question {idx + 1} must have at least 2 options'}), 400
                
                if 'correct_answer' not in question_data or question_data['correct_answer'] not in question_data['options']:
                    return jsonify({'status': False, 'error': f'Question {idx + 1} must have a correct_answer that matches one of the options'}), 400
                
                # Add question_id - use provided one or auto-generate
                question_id = question_data.get('question_id')
                if not question_id:
                    question_id = str(ObjectId())
                
                # Create new question object
                new_question = {
                    'question_id': question_id,
                    'question': question_data['question'],
                    'options': question_data['options'],
                    'correct_answer': question_data['correct_answer']
                }
                
                # Append to existing questions
                existing_questions.append(new_question)
            
            update_fields['questions'] = existing_questions
            update_fields['total_questions'] = len(existing_questions)
        
        # If no fields to update, return error
        if not update_fields:
            return jsonify({'status': False, 'error': 'No fields provided for update'}), 400
        
        # Add updated timestamp
        update_fields['updated_at'] = datetime.now().isoformat()
        update_fields['updated_by'] = admin_user.get('name', 'Administrator')
        
        # Update the quiz
        result = db.quizzes.update_one(
            {'_id': ObjectId(quiz_id)},
            {'$set': update_fields}
        )
        
        if result.modified_count == 0:
            return jsonify({'status': False, 'error': 'No changes were made to the quiz'}), 400
        
        # Fetch the updated quiz
        updated_quiz = db.quizzes.find_one({'_id': ObjectId(quiz_id)})
        
        # Prepare questions response (without correct_answer for security)
        questions_response = []
        for question in updated_quiz['questions']:
            question_item = {
                'question_id': question['question_id'],
                'question': question['question'],
                'options': question['options']
            }
            questions_response.append(question_item)
        
        return jsonify({
            'status': True,
            'message': 'Quiz updated successfully',
            'data': {
                'quiz_id': str(updated_quiz['_id']),
                'title': updated_quiz['title'],
                'total_questions': updated_quiz.get('total_questions', len(updated_quiz['questions'])),
                'created_by': updated_quiz.get('created_by', 'Administrator'),
                'created_at': updated_quiz.get('created_at'),
                'updated_by': update_fields.get('updated_by'),
                'updated_at': update_fields.get('updated_at'),
                'questions': questions_response
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

